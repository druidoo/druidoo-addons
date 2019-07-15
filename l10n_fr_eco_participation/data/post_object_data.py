# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, api
_logger = logging.getLogger(__name__)


class PostObjectData(models.TransientModel):
    _name = 'post.object.data'
    _description = 'Post Object'

    @api.model
    def load_fr_chart_template(self):
        """
        Generate eco participation account taxes
        """
        _logger.info(
            '======START LOADING CHART TEMPLATE========')
        chart_template = self.env.ref('l10n_fr.l10n_fr_pcg_chart_template')
        # chart_template.load_for_current_company(15.0, 15.0)
        company = self.env.user.company_id
        generated_tax_res = chart_template.with_context(
            active_test=False).tax_template_ids._generate_tax(company)

        template_vals = []
        account_template = self.env.ref(
            'l10n_fr_eco_participation.at_eco_participation')
        code_acc = account_template.code
        vals = chart_template._get_account_vals(
            company, account_template, code_acc, tax_template_ref={})
        template_vals.append((account_template, vals))
        account = chart_template._create_records_with_xmlid(
            'account.account', template_vals, company)
        account_ref = {account_template.id: account.id}

        # writing account values after creation of accounts
        AccountTaxObj = self.env['account.tax']
        for key, value in generated_tax_res['account_dict'].items():
            if value['refund_account_id'] or value['account_id'] \
                    or value['cash_basis_account_id'] \
                    or value['cash_basis_base_account_id']:
                AccountTaxObj.browse(key).write({
                    'refund_account_id': account_ref.get(
                        value['refund_account_id'], False),
                    'account_id': account_ref.get(value['account_id'], False),
                    'cash_basis_account_id': account_ref.get(
                        value['cash_basis_account_id'], False),
                    'cash_basis_base_account_id': account_ref.get(
                        value['cash_basis_base_account_id'], False),
                })

        self.env['ir.config_parameter'].sudo().set_param(
            'loaded_fr_chart_template', True)
        _logger.info(
            '======END LOADING CHART TEMPLATE========')
        return True

    @api.model
    def start(self):
        """
        Place all the functions need to run here
        """
        _logger.info('=====START post object=======')
        loaded_fr_chart_template = self.env[
            'ir.config_parameter'].sudo().get_param(
            'loaded_fr_chart_template'
        )
        if not loaded_fr_chart_template:
            self.load_fr_chart_template()
        _logger.info('======END post object========')
        return True
