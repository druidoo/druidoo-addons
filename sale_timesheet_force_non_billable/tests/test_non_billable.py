# Copyright (C) 2019-Today: La Louve (<https://cooplalouve.fr>)
# Copyright (C) 2019-Today: Druidoo (<https://www.druidoo.io>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.sale_timesheet.tests.common import TestCommonSaleTimesheetNoChart
from odoo import fields


class TestSaleTimesheetForceNonBillable(TestCommonSaleTimesheetNoChart):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # set up
        cls.setUpEmployees()
        cls.setUpServiceProducts()

    def setUp(self):
        super(TestSaleTimesheetForceNonBillable, self).setUp()
        self.employee = self.env.ref("hr.employee_admin")
        self.task = self.env.ref("sale_timesheet.project_task_internal")
        self.timesheet1 = self.env["account.analytic.line"].create(
            {
                "date": fields.Date.today(),
                "name": "Test Timeshsheet",
                "employee_id": self.employee.id,
                "task_id": self.task.id,
                "project_id": self.task.project_id.id,
                "force_non_billable": True,
                "unit_amount": 5.0,
            }
        )
        self.timesheet2 = self.env["account.analytic.line"].create(
            {
                "date": fields.Date.today(),
                "name": "Test Timeshsheet2",
                "employee_id": self.employee.id,
                "project_id": self.task.project_id.id,
                "force_non_billable": False,
                "unit_amount": 7.0,
            }
        )
        self.timesheet3 = self.env['account.analytic.line'].create({
            'date': fields.Date.today(),
            'name': 'Test Timeshsheet3',
            'employee_id': self.employee.id,
            'task_id': self.task.id,
            'project_id': self.task.project_id.id,
            'force_non_billable': False,
            'unit_amount': 8.0,
        })
        # create SO and confirm it
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_customer_usd.id,
            'partner_invoice_id': self.partner_customer_usd.id,
            'partner_shipping_id': self.partner_customer_usd.id,
            'pricelist_id': self.pricelist_usd.id,
        })
        so_line_ordered_global_project = self.env['sale.order.line'].create({
            'name': self.product_order_timesheet2.name,
            'product_id': self.product_order_timesheet2.id,
            'product_uom_qty': 50,
            'product_uom': self.product_order_timesheet2.uom_id.id,
            'price_unit': self.product_order_timesheet2.list_price,
            'order_id': sale_order.id,
        })
        so_line_ordered_global_project.product_id_change()
        sale_order.action_confirm()
        self.task_serv2 = self.env['project.task'].search([
            ('sale_line_id', '=', so_line_ordered_global_project.id),
        ])
        # let's log some timesheets
        # (on the project created by so_line_ordered_project_only)
        self.timesheet4 = self.env['account.analytic.line'].create({
            'name': 'Test Line',
            'project_id': self.task_serv2.project_id.id,
            'task_id': self.task_serv2.id,
            'unit_amount': 10.5,
            'employee_id': self.employee_user.id,
        })

    def test_001_check_non_billable(self):
        self.assertEquals(
            self.timesheet1.timesheet_invoice_type,
            "non_billable",
            "Timesheet must be Non Billable!",
        )

    def test_002_check_non_billable(self):
        self.assertEquals(
            self.timesheet2.timesheet_invoice_type,
            "non_billable_project",
            "Timesheet must be No task found!",
        )

    def test_001_invoiceabe_hours(self):
        """Check correct computation of field invoiceable_hours."""
        self.assertEquals(self.task.invoiceable_hours, 0)

    def test_002_invoiceabe_hours(self):
        """Check correct computation of field invoiceable_hours."""
        self.assertEqual(
            self.timesheet4.timesheet_invoice_type,
            'billable_fixed',
            "Timesheets linked to SO line with ordered product "
            "shoulbe be billable fixed"
        )
        self.assertEqual(self.task_serv2.invoiceable_hours, 10.5)
