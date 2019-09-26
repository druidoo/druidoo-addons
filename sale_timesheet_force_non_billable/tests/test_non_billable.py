# Copyright (C) 2019-Today: La Louve (<https://cooplalouve.fr>)
# Copyright (C) 2019-Today: Druidoo (<https://www.druidoo.io>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tests.common import TransactionCase
from odoo import fields


class TestSaleTimesheetForceNonBillable(TransactionCase):

    def setUp(self):
        super(TestSaleTimesheetForceNonBillable, self).setUp()
        self.employee = self.env.ref('hr.employee_admin')
        self.task = self.env.ref('sale_timesheet.project_task_internal')
        self.timesheet1 = self.env['account.analytic.line'].create({
            'date': fields.Date.today(),
            'name': 'Test Timeshsheet',
            'employee_id': self.employee.id,
            'task_id': self.task.id,
            'project_id': self.task.project_id.id,
            'force_non_billable': True,
            'unit_amount': 5.0,
        })
        self.timesheet2 = self.env['account.analytic.line'].create({
            'date': fields.Date.today(),
            'name': 'Test Timeshsheet2',
            'employee_id': self.employee.id,
            'project_id': self.task.project_id.id,
            'force_non_billable': False,
            'unit_amount': 7.0,
        })

    def test_001_check_non_billable(self):
        self.assertEquals(self.timesheet1.timesheet_invoice_type,
                          'non_billable',
                          'Timesheet must be Non Billable!')

    def test_002_check_non_billable(self):
        self.assertEquals(self.timesheet2.timesheet_invoice_type,
                          'non_billable_project',
                          'Timesheet must be No task found!')
