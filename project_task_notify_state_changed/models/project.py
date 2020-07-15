from odoo import api, fields, models


class Task(models.Model):
    _inherit = 'project.task'

    notify_stage_changed = fields.Boolean(
        default=True,
        track_visibility='onchange',
    )

    @api.multi
    def _track_template(self, tracking):
        res = super()._track_template(tracking)
        if not all(self.mapped('notify_stage_changed')):
            res.pop('stage_id', None)
        return res

    @api.multi
    def toggle_silent(self):
        self.ensure_one()
        self.notify_stage_changed = not self.notify_stage_changed
        return True
