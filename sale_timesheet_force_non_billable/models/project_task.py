# Copyright (C) 2019-Today: Druidoo (<https://www.druidoo.io>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    invoiceable_hours = fields.Float(
        compute='_compute_invoiceable_hours', store=True
    )

    @api.depends('timesheet_ids')
    def _compute_invoiceable_hours(self):
        """Compute value for field invoiceable_hours."""
        for record in self:
            record.invoiceable_hours = sum(
                record.timesheet_ids.filtered(
                    lambda t: t.timesheet_invoice_type != 'non_billable'
                ).mapped('unit_amount')
            )
