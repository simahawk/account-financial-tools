# -*- coding: utf-8 -*-
#
#
#    Authors: Adrien Peiffer
#    Copyright (c) 2014 Acsone SA/NV (http://www.acsone.eu)
#    All Rights Reserved
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsibility of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs.
#    End users who are looking for a ready-to-use solution with commercial
#    guarantees and support are strongly advised to contact a Free Software
#    Service Company.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#


from openerp.osv import fields, orm
from openerp.tools.translate import _


class stock_picking(orm.Model):
    _inherit = 'stock.picking'

    def _get_message(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for stock_picking in self.browse(cr, uid, ids):
            message = ""
            if (stock_picking.partner_id.commercial_partner_id.blocked_customer == True):
                message = _("Warning ! This customer is blocked !")
            res[stock_picking.id] = message
        return res

    _columns = {'blocked_message': fields.function(_get_message, type="char", string='Message'),
                }

    def do_transfer(self, cr, uid, ids, context={}):
        stock_picking_obj = self.browse(cr, uid, ids, context=context)[0]
        if context.get('force', False) != True:
            res = super(stock_picking, self).do_transfer(cr, uid, ids, context=context)
            if (stock_picking_obj.partner_id.commercial_partner_id.blocked_customer == True):
                raise orm.except_orm(_('Warning !'), _("This customer is blocked or this confirmation implies to blocked it"))
            else:
                return res
        else:
            if (context.get('validate', False) == False):
                context.update({'force': False})
                values = {
                            'stock_picking_id': stock_picking_obj.id,
                        }

                wizard_id = self.pool.get('warning.force.picking.wizard').create(cr, uid, values, context=context)
                return {
                    'name': _('Force Picking'),
                    'view_mode': 'form',
                    'view_id': False,
                    'view_type': 'form',
                    'res_model': 'warning.force.picking.wizard',
                    'res_id': wizard_id,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'domain': '[]',
                    'context': context,
                }
            else:
                context.update({'validate': False, 'force': False})
                return super(stock_picking, self).do_transfer(cr, uid, ids, context=context)


class warning_force_picking_wizard(orm.TransientModel):
    _name = 'warning.force.picking.wizard'
    _columns = {'stock_picking_id': fields.many2one('stock.picking', string='Picking', required=True),
                }

    def validate(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids, context=context)
        stock_move_model = self.pool.get('stock.move')
        stock_move_ids = stock_move_model.search(cr, uid, [('picking_id.id', '=', this.stock_picking_id.id), ('procurement_id', '<>', False)])
        amount_order = 0.0
        for stock_move in stock_move_model.browse(cr, uid, stock_move_ids, context=context):
            sale_order_line = stock_move.procurement_id.sale_line_id
            tax_ids = sale_order_line.tax_id
            tax = 1.0
            for tax_id in tax_ids:
                tax = tax + tax_id.amount
            amount_order = amount_order + sale_order_line.price_subtotal * tax

        if this.stock_picking_id.partner_id.commercial_partner_id.level_amount is None:
            amount = _('Manual Blocking')
        else:
            amount = amount_order
        diff = this.stock_picking_id.partner_id.commercial_partner_id.credit_limit - this.stock_picking_id.partner_id.commercial_partner_id.level_amount
        if (diff > 0):
            amount = amount - diff
        self.pool.get('force.tracking').create(cr, uid, {'user_id': uid,
                                                        'type': 'delivery_order',
                                                        'source_document': this.stock_picking_id.name,
                                                        'partner_id': this.stock_picking_id.partner_id.commercial_partner_id.id,
                                                        'amount': str(amount),
                                                        })
        context.update({'validate': True, 'force': True})
        return self.pool.get('stock.picking').do_transfer(cr, uid, [this.stock_picking_id.id], context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: