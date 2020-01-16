# Copyright 2019 Druidoo - Iván Todorovich
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestProductAttributeMassEdit(TransactionCase):
    def setUp(self):
        super(TestProductAttributeMassEdit, self).setUp()

        self.product1 = self.env.ref(
            "product.product_product_1_product_template"
        )
        self.product2 = self.env.ref(
            "product.product_product_2_product_template"
        )
        self.product3 = self.env.ref(
            "product.product_product_3_product_template"
        )
        self.product4 = self.env.ref(
            "product.product_product_4_product_template"
        )

        self.product_tmpl_ids = (
            self.product1 + self.product2 + self.product3 + self.product4
        )

        self.attribute1 = self.env["product.attribute"].create(
            {
                "name": "Variant Attribute",
                "create_variant": "always",
                "value_ids": [
                    (0, 0, {"name": "Variant Value 1"}),
                    (0, 0, {"name": "Variant Value 2"}),
                ],
            }
        )

        self.attribute2 = self.env["product.attribute"].create(
            {
                "name": "Informational Attribute",
                "create_variant": "no_variant",
            }
        )

        self.attribute2_1 = self.env["product.attribute.value"].create({
            "attribute_id": self.attribute2.id,
            "name": "Info Value 1",
        })

        self.attribute2_2 = self.env["product.attribute.value"].create({
            "attribute_id": self.attribute2.id,
            "name": "Info Value 2",
        })

    def get_wizard(self):
        return (
            self.env["product.attribute.mass.edit.wizard"]
            .with_context(active_ids=self.product_tmpl_ids.ids)
            .create({})
        )

    def test_without_variant_creation(self):
        # Test adding new values
        wizard = self.get_wizard()
        wizard.line_ids = [
            (
                0,
                0,
                {
                    "action": "add",
                    "attribute_id": self.attribute2.id,
                    "value_ids": self.attribute2_1,
                },
            )
        ]
        wizard.confirm()
        for product in self.product_tmpl_ids:
            attribute_line_id = self.product1.attribute_line_ids.filtered(
                lambda l: l.attribute_id == self.attribute2
            )
            self.assertEqual(attribute_line_id.value_ids, self.attribute2_1)

        # Test replacing values
        wizard = self.get_wizard()
        wizard.line_ids = [
            (
                0,
                0,
                {
                    "action": "replace",
                    "attribute_id": self.attribute2.id,
                    "value_ids": self.attribute2.value_ids,
                },
            )
        ]
        wizard.confirm()
        for product in self.product_tmpl_ids:
            attribute_line_id = self.product1.attribute_line_ids.filtered(
                lambda l: l.attribute_id == self.attribute2
            )
            self.assertEqual(
                attribute_line_id.value_ids, self.attribute2.value_ids
            )

        # Test removing values
        wizard = self.get_wizard()
        wizard.line_ids = [
            (
                0,
                0,
                {
                    "action": "remove",
                    "attribute_id": self.attribute2.id,
                    "value_ids": self.attribute2_1,
                },
            )
        ]
        wizard.confirm()
        for product in self.product_tmpl_ids:
            attribute_line_id = self.product1.attribute_line_ids.filtered(
                lambda l: l.attribute_id == self.attribute2
            )
            self.assertEqual(attribute_line_id.value_ids, self.attribute2_2)

        # Test removing attribute
        wizard = self.get_wizard()
        wizard.line_ids = [
            (
                0,
                0,
                {
                    "action": "replace",
                    "attribute_id": self.attribute2.id,
                    "value_ids": False,
                },
            )
        ]
        wizard.confirm()
        for product in self.product_tmpl_ids:
            attribute_line_id = self.product1.attribute_line_ids.filtered(
                lambda l: l.attribute_id == self.attribute2
            )
            self.assertFalse(attribute_line_id)

    def test_variant_create(self):
        # Test adding new values should fail without force
        wizard = self.get_wizard()
        wizard.line_ids = [
            (
                0,
                0,
                {
                    "action": "add",
                    "attribute_id": self.attribute1.id,
                    "value_ids": self.attribute1.value_ids,
                },
            )
        ]
        with self.assertRaises(UserError):
            wizard.confirm()

        # Test adding new values should succeed with force
        wizard = self.get_wizard()
        wizard.line_ids = [
            (
                0,
                0,
                {
                    "action": "add",
                    "attribute_id": self.attribute1.id,
                    "value_ids": self.attribute1.value_ids,
                },
            )
        ]
        wizard.force = True
        wizard.confirm()

        for product in self.product_tmpl_ids:
            attribute_line_id = self.product1.attribute_line_ids.filtered(
                lambda l: l.attribute_id == self.attribute1
            )
            self.assertEqual(
                attribute_line_id.value_ids, self.attribute1.value_ids
            )
