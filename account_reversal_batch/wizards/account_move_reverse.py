# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons.queue_job.job import job


class AccountMoveReverse(models.TransientModel):

    _inherit = 'account.move.reverse'

    asynchronous = fields.Boolean(
        string="Use asynchronous process"
    )

    @api.multi
    def action_reverse(self):
        async_wizards = self.env['account.move.reverse']
        wizards = self.env['account.move.reverse']
        active_ids = self.env.context.get('active_ids')

        for wizard in self:
            if wizard.asynchronous:
                async_wizards |= wizard
            else:
                wizards |= wizard

        for async_wizard in async_wizards:
            async_wizard.with_delay().process_wizard(active_ids)

        return super(AccountMoveReverse, wizards).action_reverse()

    @job(default_channel='root.account_reversal')
    @api.multi
    def process_wizard(self, move_ids):
        self.ensure_one()
        moves = self.env['account.move'].browse(move_ids)
        reversals = moves.create_reversals(
            date=self.date, journal=self.journal_id,
            move_prefix=self.move_prefix, line_prefix=self.line_prefix,
            reconcile=self.reconcile)
        return reversals
