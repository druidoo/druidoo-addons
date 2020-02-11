from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class POSVoucher(models.Model):
    _name = 'pos.voucher'
    _inherit = ['mail.thread']
    _rec_name = 'code'
    _description = 'POS Voucher'

    code = fields.Char(required=True, default='/', copy=False)
    start_date = fields.Datetime(required=True)
    end_date = fields.Datetime()
    type_id = fields.Many2one('pos.voucher.type', 'Type', required=True)
    partner_id = fields.Many2one('res.partner', 'Customer', required=True)
    consume_date = fields.Datetime(
        'Consumed on',
        compute='_compute_date_amount',
        store=True,
    )
    discount_type = fields.Selection([
        ('fixed', 'Fixed')
        ],
        default='fixed',
    )
    total_amount = fields.Monetary()
    pending_amount = fields.Monetary(
        compute='_compute_date_amount',
        store=True,
    )
    history_ids = fields.One2many(
        'pos.voucher.history',
        'pos_voucher_id',
        string='Voucher History',
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('validated', 'Validated'),
        ('partially_consumed', 'Partially Consumed'),
        ('consumed', 'Consumed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ],
        default='draft',
        required=True,
        copy=False,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.user.company_id.id,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Account Currency',
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    pos_order_line_id = fields.Many2one(
        'pos.order.line',
        string='POS Order Line',
        help='If this voucher was created from POS, it stores the line '
             'that created this voucher.',
    )
    pos_order_id = fields.Many2one(
        related='pos_order_line_id.order_id',
        help='If this voucher was created from POS, it stores the order '
             'that created this voucher.',
    )

    _sql_constraints = [
        ('unique_code', 'unique (code)',
         'The Code of the Voucher must be unique!'),
        ('check_pending_amount', 'check(pending_amount>=0)',
         'Can not Apply more than allowed Amount!')
    ]

    @api.depends('total_amount', 'history_ids',
                 'history_ids.amount',
                 'history_ids.consumed_date')
    def _compute_date_amount(self):
        # TODO: Use read_group to improve performance
        for rec in self:
            consumed_amount = sum(rec.history_ids.mapped('amount'))
            rec.pending_amount = rec.total_amount - consumed_amount
            if rec.history_ids:
                consume_date = max(rec.history_ids.mapped('consumed_date'))
                rec.consume_date = consume_date

    @api.multi
    def action_validate(self):
        states = list(set(self.mapped('state')))
        if len(states) > 1 or states[0] != 'draft':
            raise ValidationError(_(
                'All selected records has to be in Draft State!'))
        for rec in self:
            vals = {'state': 'validated'}
            if not rec.code or rec.code == '/':
                code = rec.type_id.sequence_id.next_by_code(
                    rec.type_id.sequence_id.code)
                vals.update({'code': code})
            rec.write(vals)
        return True

    @api.multi
    def action_consume(self):
        self.ensure_one()
        if self.pending_amount > 0:
            state = 'partially_consumed'
        else:
            state = 'consumed'
        return self.write({'state': state})

    @api.multi
    def action_force_expired(self):
        self.write({'state': 'expired', 'end_date': fields.Datetime.today()})
        return True

    @api.multi
    def action_cancel(self):
        if self.filtered('pos_order_line_id'):
            raise ValidationError(_(
                'You can\'t cancel a voucher generated from a POS Order'))
        self.write({'state': 'cancelled'})
        return True

    @api.multi
    def action_draft(self):
        if self.filtered('history_ids'):
            raise ValidationError(_(
                'Can not set to Draft as Consume History is '
                'created for the voucher!'))
        self.write({'state': 'draft'})
        return True

    @api.model
    def get_voucher_by_code(self, code, partner_id):
        if not code or not partner_id:
            return -1, 'Customer is not set!'
        voucher = self.env['pos.voucher'].search(
            [('code', '=', code), ('partner_id', '=', partner_id)], limit=1)
        if not voucher:
            return -1, "Voucher code with the customer dosn't exist!"
        else:
            if voucher.state in ('validated', 'partially_consumed'):
                return 1, voucher.read([])[0]
            else:
                return -1, 'Voucher is %s!' % str(voucher.state).title()

    @api.model
    def get_pos_voucher_print(self, pos_ref=''):
        ret_list = []
        if pos_ref:
            pos_order = self.env['pos.order'].search([
                ('pos_reference', '=', pos_ref)])
            if pos_order:
                pos_voucher_ids = pos_order.mapped('lines.pos_voucher_id')
                for pos_voucher in pos_voucher_ids:
                    pos_vals = {
                        'code': pos_voucher.code,
                        'pending_amount': pos_voucher.pending_amount,
                        'end_date': pos_voucher.end_date,
                    }
                    if pos_voucher.company_id:
                        pos_vals.update({
                            'company_name': pos_voucher.company_id.name,
                            'company_phone':
                            pos_voucher.company_id.phone or '',
                            'company_email':
                            pos_voucher.company_id.email or '',
                            'company_website':
                            pos_voucher.company_id.website or '',
                        })
                    ret_list.append(pos_vals)
        return ret_list

    @api.model
    def generate_code_voucher_for_print(self, voucher_type_id=False):
        voucher_code = ''
        voucher_type_id_brw = self.env['pos.voucher.type'].browse(
            voucher_type_id)
        if voucher_type_id_brw:
            voucher_code = voucher_type_id_brw.sequence_id.next_by_code(
                voucher_type_id_brw.sequence_id.code)
        return voucher_code
