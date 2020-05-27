# Copyright (C) 2019-Today: Druidoo (<https://www.druidoo.io>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    force_non_billable = fields.Boolean(
        default=False,
        track_visibility='onchange'
    )
    
    timesheet_invoice_type = fields.Selection(compute_sudo=True)

    @api.multi
    @api.depends('so_line.product_id', 'project_id', 'task_id',
                 'force_non_billable')
    def _compute_timesheet_invoice_type(self):
        timesheets = self.filtered(lambda t: t.force_non_billable)
        timesheets.write({'timesheet_invoice_type': 'non_billable'})
        return super(AccountAnalyticLine, self - timesheets).\
            _compute_timesheet_invoice_type()
