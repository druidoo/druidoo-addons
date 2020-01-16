# Copyright 2019 Druidoo - Iván Todorovich
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class ProductAttributeMassEditWizard(models.TransientModel):
    _name = "product.attribute.mass.edit.wizard"
    _description = "Product Attribute Mass Edit Wizard"

    product_tmpl_ids = fields.Many2many(
        "product.template", string="Product Templates", readonly=True,
    )

    line_ids = fields.One2many(
        "product.attribute.mass.edit.wizard.line",
        "wizard_id",
        "Operations",
        required=True,
    )

    force = fields.Boolean(
        "Allow to modify attributes that create/delete variants"
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res_ids = self._context.get("active_ids")
        res.update(
            {"product_tmpl_ids": res_ids,}
        )
        return res

    def validate_safe(self):
        self.ensure_one()
        for line in self.line_ids:
            if line.attribute_id.create_variant == "always":
                raise UserError(
                    _(
                        "Unable to mass edit attributes that create variants\n"
                        'You\'re trying to edit attribute "%s", which always '
                        "creates new variants."
                        "This is not recommended. If you really need to do it "
                        "run the wizard in debug mode and enable the option."
                    )
                    % line.attribute_id.name
                )
            elif line.attribute_id.create_variant == "dynamic":
                if line.action != "add":
                    raise UserError(
                        _(
                            "Unable to mass edit attributes that create variants\n"
                            'You\'re trying to remove or replace values for "%s", '
                            "which creates variants dynamically.\n"
                            "This is not recommended. If you really need to do it "
                            "run the wizard in debug mode and enable the option."
                        )
                        % line.attribute_id.name
                    )

    def confirm(self):
        self.ensure_one()
        # prefetch
        self.product_tmpl_ids.mapped("attribute_line_ids.value_ids.id")
        self.product_tmpl_ids.mapped(
            "attribute_line_ids.attribute_id.create_variant"
        )
        if not self.force:
            self.validate_safe()
        for product_tmpl_id in self.product_tmpl_ids:
            self.update_attribute_lines(product_tmpl_id)

    def update_attribute_lines(self, product_tmpl_id):
        """ We need to compute everything and apply a single write.
        This way create_variant_ids is called only once per template """
        operations = []
        for line in self.line_ids:
            current_line = product_tmpl_id.attribute_line_ids.filtered(
                lambda l: l.attribute_id == line.attribute_id
            )
            if line.action == "add":
                if not current_line:
                    # Create new attribute line
                    operations += [
                        (
                            0,
                            0,
                            {
                                "attribute_id": line.attribute_id.id,
                                "value_ids": [(6, 0, line.value_ids.ids)],
                            },
                        )
                    ]
                else:
                    # Add values to the existing line
                    operations += [
                        (
                            1,
                            current_line.id,
                            {
                                "value_ids": [
                                    (4, v.id)
                                    for v in line.value_ids
                                    if v not in current_line.value_ids
                                ]
                            },
                        )
                    ]
            if line.action == "remove":
                if current_line:
                    if len(current_line.value_ids - line.value_ids) == 0:
                        # Remove attribute line
                        operations += [(2, current_line.id)]
                    else:
                        # Remove values from line
                        operations += [
                            (
                                1,
                                current_line.id,
                                {
                                    "value_ids": [
                                        (3, v.id)
                                        for v in line.value_ids
                                        if v in current_line.value_ids
                                    ]
                                },
                            )
                        ]
            if line.action == "replace":
                if current_line and line.value_ids:
                    # Replace values from existing line
                    operations += [
                        (
                            1,
                            current_line.id,
                            {"value_ids": [(6, 0, line.value_ids.ids)],},
                        )
                    ]
                elif current_line and not line.value_ids:
                    # Remove attribute line
                    operations += [(2, current_line.id)]
                elif not current_line and line.value_ids:
                    # Create new attribute line
                    operations += [
                        (
                            0,
                            0,
                            {
                                "attribute_id": line.attribute_id.id,
                                "value_ids": [(6, 0, line.value_ids.ids)],
                            },
                        )
                    ]
        if operations:
            product_tmpl_id.write({"attribute_line_ids": operations})


class ProductAttributeMassEditWizardLine(models.TransientModel):
    _name = "product.attribute.mass.edit.wizard.line"
    _description = "Product Attribute Mass Edit Wizard Line"

    wizard_id = fields.Many2one(
        "product.attribute.mass.edit.wizard",
        readonly=True,
        required=True,
        index=True,
        ondelete="cascade",
    )

    force = fields.Boolean(related="wizard_id.force")

    action = fields.Selection(
        [
            ("add", "Add values"),
            ("remove", "Remove values"),
            ("replace", "Replace values"),
        ],
        string="Action",
        required=True,
    )

    attribute_id = fields.Many2one(
        "product.attribute", "Attribute", required=True,
    )

    value_ids = fields.Many2many(
        "product.attribute.value",
        "product_attribute_mass_edit_wizard_line_pav_rel",
        string="Values",
    )
