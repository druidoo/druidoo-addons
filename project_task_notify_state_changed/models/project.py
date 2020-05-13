from odoo import fields, models


class Task(models.Model):
    _inherit = "project.task"

    notify_stage_changed = fields.Boolean(
        default=True, track_visibility="onchange",
    )

    def _track_template(self, tracking):
        self.ensure_one()
        res = super()._track_template(tracking)
        if not self.notify_stage_changed:
            res.pop("stage_id", None)
        return res

    def toggle_silent(self):
        self.ensure_one()
        self.notify_stage_changed = not self.notify_stage_changed
        return True
