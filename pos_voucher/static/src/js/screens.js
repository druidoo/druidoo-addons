odoo.define('pos_voucher.screens', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var models = require('point_of_sale.models');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;

    var voucherListScreenWidget = screens.ScreenWidget.extend({
        template: 'voucherListScreenWidget',
        init: function (parent, options) {
            this._super(parent, options);
            this.voucher_cache = new screens.DomCache();
            this.new_voucher = null;
        },
        auto_back: true,
        show: function () {
            var self = this;
            this._super();
            this.renderElement();
            this.new_voucher = null;
            this.old_voucher = this.pos.get_order().voucher_id;
            this.$('.back').click(function () {
                self.gui.back();
                this.new_voucher = null;
            });
            this.$('.next').click(function () {
                var current_order = self.pos.get('selectedOrder');
                var voucher = self.new_voucher;
                if (!voucher)
                {
                    return self.gui.show_popup('alert', {
                                title: _t('Warning'),
                                body: _t('Please select a Voucher'),
                            });
                }
                current_order.voucher_id = voucher.id;
                var voucher_register = null;
                if (voucher.type_id)
                {
                    var voucher_type_search = self.pos.voucher_type_by_id[voucher.type_id[0]];
                    if(voucher_type_search)
                    {
                        voucher_register = _.find(self.pos.cashregisters, function (cashregister) {
                            return cashregister.journal['id'] == voucher_type_search['journal_id'][0];
                        });
                    }
                }
                if (!voucher_register){
                    return self.gui.show_popup('alert', {
                                title: _t('Configuration Warning'),
                                body: _t('Please configure '+ voucher_type_search['journal_id'][1] + ' as a payment method in your POS.'),
                            });
                }
                if (voucher['partner_id'] && voucher['partner_id'][0]) {
                    var client = self.pos.db.get_partner_by_id(voucher['partner_id'][0]);
                    if (client) {
                        current_order.set_client(client)
                    }
                }
                var amount = voucher.pending_amount;
                /*var paymentlines = current_order.paymentlines;
                for (var i = 0; i < paymentlines.models.length; i++) {
                    var payment_line = paymentlines.models[i];
                    if (payment_line.cashregister.journal['id'] == voucher_register['journal'].id) {
                        payment_line.destroy();
                    }
                }*/
                var voucher_paymentline = new models.Paymentline({}, {
                    order: current_order,
                    cashregister: voucher_register,
                    pos: self.pos
                });
                var due = current_order.get_due();
                if (amount >= due) {
                    voucher_paymentline.set_amount(due);
                } else {
                    voucher_paymentline.set_amount(amount);
                }
                voucher_paymentline['voucher_id'] = voucher['id'];
                voucher_paymentline['voucher_code'] = voucher['code'];
                current_order.paymentlines.add(voucher_paymentline);
                current_order.trigger('change', current_order);
                self.gui.back();
            });
            var partner_id = this.pos.get('selectedOrder').get_client();
            if (partner_id) {
                var vouchers = this.pos.voucher_by_customer[partner_id.id];
                if (vouchers) {
                    this.render_list(vouchers);
                }
            }
            this.$('.voucher-list-contents').delegate('.client-list','click',function(event){
                self.line_select(event,$(this),parseInt($(this).data('id')));
            });
            var search_timeout = null;
            if (this.pos.config.iface_vkeyboard &&
                this.chrome.widget.keyboard) {
                this.chrome.widget.keyboard.connect(
                    this.$('.searchbox input'));
            }
            this.$('.searchbox input').on('keypress', function (event) {
                clearTimeout(search_timeout);
                var searchbox = this;
                search_timeout = setTimeout(function () {
                    self.perform_search(searchbox.value, event.which === 13);
                }, 70);
            });
            this.$('.searchbox .search-clear').click(function () {
                self.clear_search();
            });
        },
        hide: function () {
            this._super();
        },
        render_list: function (vouchers) {
            var contents = this.$el[0].querySelector('.voucher-list-contents');
            contents.innerHTML = "";
            for (var i = 0, len = Math.min(vouchers.length, 1000);
                i < len; i++) {
                var voucher = vouchers[i];
                var voucherline_node = this.voucher_cache.get_node(voucher.id);
                var voucherline = null;
                if (!voucherline_node) {
                    var voucherline_html = QWeb.render('voucherLine',
                        {widget: this, voucher:vouchers[i]});
                    var voucherline = document.createElement('tbody');
                    voucherline.innerHTML = voucherline_html;
                    voucherline = voucherline.childNodes[1];
                    this.voucher_cache.cache_node(voucher.id, voucherline);
                }
                if (voucherline) {
                    if( voucher.id === this.old_voucher ){
                        voucherline.classList.add('highlight');
                    }else{
                        voucherline.classList.remove('highlight');
                    }
                    contents.appendChild(voucherline);
                }
            }
        },
        has_voucher_changed: function(){
            if( this.old_voucher && this.new_voucher ){
                return this.old_voucher.id !== this.new_voucher.id;
            }else{
                return !!this.old_voucher !== !!this.new_voucher;
            }
        },
        line_select: function(event,$line,id){
            var voucher = this.pos.voucher_by_id[id];
            this.$('.client-list .lowlight').removeClass('lowlight');
            if ( $line.hasClass('highlight') ){
                $line.removeClass('highlight');
                $line.addClass('lowlight');
                this.new_voucher = null;
            }else{
                this.$('.client-list .highlight').removeClass('highlight');
                $line.addClass('highlight');
                var y = event.pageY - $line.parent().offset().top;
                this.new_voucher = voucher;
            }
        },
        close: function () {
            this._super();
            if (this.pos.config.iface_vkeyboard &&
                this.chrome.widget.keyboard) {
                this.chrome.widget.keyboard.hide();
            }
        },
    });
    gui.define_screen({name:'voucherlist', widget: voucherListScreenWidget});
    screens.PaymentScreenWidget.include({
        renderElement: function () {
            var self = this;
            this._super();
            this.$('.customer_vouchers').click( function () {
                //  Reload vouchers
                var current_order = self.pos.get('selectedOrder');
                var voucher_ids = [];
                var paymentlines = current_order.paymentlines;
                for (var i = 0; i < paymentlines.models.length; i++) {
                    var payment_line = paymentlines.models[i];
                    if (payment_line.voucher_id) {
                        voucher_ids.push(payment_line.voucher_id);
                    }
                }
                self._rpc({
                    model: 'pos.voucher',
                    method: 'search_read',
                    fields: ['code', 'type_id', 'partner_id', 'start_date',
                        'end_date', 'pending_amount', 'total_amount'],
                    domain: [['state', 'in', ['validated',
                        'partially_consumed']],['id','not in', voucher_ids]],
                })
                    .then(function (vouchers) {
                        self.pos.vouchers = vouchers;
                        self.pos.voucher_by_id = {};
                        self.pos.voucher_by_customer = {};
                        for (var x = 0; x < vouchers.length; x++) {
                            self.gui.screen_instances.voucherlist
                                .voucher_cache.clear_node(vouchers[x].id);
                            self.pos.voucher_by_id[vouchers[x].id] =
                                vouchers[x];
                            if (self.pos.voucher_by_customer[
                                vouchers[x].partner_id[0]]) {
                                self.pos.voucher_by_customer[
                                    vouchers[x].partner_id[0]].push(
                                    vouchers[x]);
                            } else {
                                self.pos.voucher_by_customer[
                                    vouchers[x].partner_id[0]] = [vouchers[x]];
                            }
                        }
                        self.pos.gui.show_screen('voucherlist');
                    }).fail(function () {
                        self.pos.gui.show_screen('voucherlist');
                    });
            });
            //  Input manual voucher
            this.$('.voucher_redeem').click(function () {
                self.hide();
                return self.pos.gui.show_popup('alert_input', {
                    title: _t('Voucher'),
                    body: _t('Please input code of a voucher.'),
                    confirm: function (code) {
                        self.show();
                        self.renderElement();
                        if (code) {
                            var current_order = self.pos.get('selectedOrder');
                            var partner_id = false;
                            if (current_order.get_client()) {
                                partner_id = current_order.get_client().id;
                            }
                            return rpc.query({
                                model: 'pos.voucher',
                                method: 'get_voucher_by_code',
                                args: [code, partner_id],
                            }).then(function (voucher_result) {
                                if (voucher_result[0] === -1) {
                                    return self.gui.show_popup('confirm', {
                                        title: 'Warning',
                                        body: voucher_result[1],
                                    });
                                }
                                var voucher = voucher_result[1];
                                current_order.voucher_id = voucher.id;
                                var voucher_register = null;
                                if (voucher.type_id) {
                                    var voucher_type_search =
                                    self.pos.voucher_type_by_id[
                                        voucher.type_id[0]];
                                    if (voucher_type_search) {
                                        voucher_register = _.find(
                                            self.pos.cashregisters,
                                            function (cashregister) {
                                                return cashregister
                                                    .journal.id ===
                                                        voucher_type_search
                                                            .journal_id[0];
                                            });
                                    }
                                }
                                if (!voucher_register) {
                                    return self.gui.show_popup('alert', {
                                        title: _t('Configuration Warning'),
                                        body: _t('Please configure '+
                                        voucher_type_search
                                            .journal_id[1] +
                                            ' as a payment method' +
                                            'in your POS.'),
                                    });
                                }
                                if (voucher.partner_id &&
                                    voucher.partner_id[0]) {
                                    var client =
                                    self.pos.db.get_partner_by_id(
                                        voucher.partner_id[0]);
                                    if (client) {
                                        current_order.set_client(client);
                                    }
                                }
                                var amount = voucher.pending_amount;
                                var paymentlines =
                                    current_order.paymentlines;
                                for (var i = 0;
                                    i < paymentlines.models.length; i++) {
                                    var payment_line =
                                        paymentlines.models[i];
                                    if (payment_line.cashregister
                                        .journal.id === voucher_register
                                        .journal.id) {
                                        payment_line.destroy();
                                    }
                                }
                                var voucher_paymentline =
                                new models.Paymentline({}, {
                                    order: current_order,
                                    cashregister: voucher_register,
                                    pos: self.pos,
                                });
                                var due = current_order.get_due();
                                if (amount >= due) {
                                    voucher_paymentline.set_amount(due);
                                } else {
                                    voucher_paymentline.set_amount(amount);
                                }
                                voucher_paymentline.voucher_id = voucher.id;
                                voucher_paymentline.voucher_code =
                                    voucher.code;
                                current_order.paymentlines.add(
                                    voucher_paymentline);
                                current_order.trigger('change',
                                    current_order);
                                self.render_paymentlines();
                                self.$('.paymentline.selected .edit').text(
                                    self.format_currency_no_symbol(amount));
                            }).fail(function (type, error) {
                                return self.pos.query_backend_fail(type, error);
                            });
                        }
                        return false;
                    },
                    cancel: function () {
                        self.show();
                        self.renderElement();
                    },
                });
            });
        },
        //  Hide voucher journals from available payment lines
        render_paymentlines: function () {
            this._super();
            var voucher_journal = _.find(this.pos.cashregisters,
                function (cashregister) {
                    return cashregister.journal.pos_method_type === 'voucher';
                });
            if (voucher_journal) {
                var voucher_journal_id = voucher_journal.journal.id;
                var voucher_journal_content =
                    $("[data-id='" + voucher_journal_id + "']");
                voucher_journal_content.addClass('oe_hidden');
            }
        },
        get_voucher_amount_order: function (voucher_type_search) {
            var voucher_amount = 0;
            var current_order = this.pos.get_order();
            var paymentlines = current_order.paymentlines;
            for (var i = 0; i < paymentlines.models.length; i++) {
                var payment_line = paymentlines.models[i];
                if (payment_line.cashregister.journal.id ===
                    voucher_type_search.journal_id[0]) {
                    if (payment_line.amount >
                        this.pos.voucher_by_id[current_order
                            .voucher_id].pending_amount) {
                        return this.gui.show_popup('alert', {
                            title: _t('Configuration Warning'),
                            body: _t('The amount of ' +
                            voucher_type_search.journal_id[1] +
                            ' must be less than a voucher amount!'),
                        });
                    }
                    voucher_amount = payment_line.amount;
                }
            }
            return voucher_amount;
        },
        validate_order: function (force_validation) {
            var current_order = this.pos.get_order();
            if (current_order.is_paid() && current_order.voucher_id) {
                var voucher = this.pos.voucher_by_id[current_order.voucher_id];
                if (voucher) {
                    if (current_order.get_client()) {
                        var voucher_type_search = this.pos.voucher_type_by_id[
                            voucher.type_id[0]];
                        var voucher_amount = this.get_voucher_amount_order(
                            voucher_type_search);
                        this.pos.voucher_by_customer[current_order
                            .get_client().id].pending_amount -= voucher_amount;
                        this.pos.voucher_by_id[current_order.voucher_id]
                            .pending_amount -= voucher_amount;
                        if (this.gui.screen_instances.voucherlist) {
                            this.gui.screen_instances.voucherlist
                                .voucher_cache.clear_node(voucher.id);
                        }
                    }
                }
            }
            // Get code for generated vouchers. This currently means nothing
            // because it's just getting a sequence, but not really
            // creating the voucher that will happen after.
            /*  if (current_order.is_voucher_order() == 1) {
                this.update_voucher_code();
                setTimeout(function(){
                    if (this.order_is_valid(force_validation)) {
                        this.finalize_validation();
                    }
                }.bind(this),2000);
            } else {
                this._super(force_validation);
            }*/
            var self = this;
            var order = self.pos.get_order();
            if (order.is_voucher_order() === 1) {
                var done_ret = new $.Deferred();
                var _super=this._super.bind(this);
                var count = 0;
                _.each(order.orderlines.models, function (line) {
                    if (line && line.voucher_type_id &&
                        line.pos_voucher_code === '') {
                        count += 1;
                        var records = self._rpc({
                            model: 'pos.voucher',
                            method: 'generate_code_voucher_for_print',
                            args: [line.voucher_type_id],
                        });
                        $.when(records.then(function (pos_voucher_code) {
                            line.pos_voucher_code=pos_voucher_code;
                        })).done(function () {
                            count -= 1;
                            if (count===0) {
                                done_ret.resolve();
                            }
                        });
                    }
                });
                order.trigger('change');
                $.when(done_ret).done(function () {
                    return _super(force_validation);
                });
            } else {
                this._super();
            }
        },
        //  Updates order line information with voucher code
        /*  update_voucher_code: function() {
            var self = this;
            var order = self.pos.get_order();
            _.each(order.orderlines.models, function (line) {
                if (line && line.voucher_type_id && line.pos_voucher_code ==
                    ''){
                    var records = self._rpc({
                            model: 'pos.voucher',
                            method: 'generate_code_voucher_for_print',
                            args: [line.voucher_type_id],
                        });
                    records.then(function (pos_voucher_code) {
                        line['pos_voucher_code'] = pos_voucher_code;
                    });
                }
            });
            order.trigger('change');
        },*/
    });
    screens.ClientListScreenWidget.include({
        // When changing a customer, we want to destroy the voucher
        // payment lines
        // because they could be linked to another customer.
        // Just in case we destroy all
        has_client_changed: function () {
            var current_order = this.pos.get('selectedOrder');
            var paymentlines = current_order.paymentlines;
            for (var i = 0; i < paymentlines.models.length; i++) {
                var payment_line = paymentlines.models[i];
                payment_line.destroy();
            }
            return this._super();
        },
    });
    screens.ReceiptScreenWidget.include({
        // Extend to add voucher data
        // Notes: This happens after update_voucher_code()
        // TODO: Try to fetch voucher real data instead of using order lines
        get_receipt_render_env: function () {
            var res = this._super.apply(this, arguments);
            var order = this.pos.get_order();
            var orderlines = order.get_orderlines();
            var vouchers = [];
            for (var i = 0, len = orderlines.length; i < len; i++) {
                var orderline = orderlines[i];
                if (orderline && orderline.voucher_type_id) {
                    var line_dict = {
                        'code': orderline.pos_voucher_code,
                        'pending_amount': orderline.get_price_with_tax(),
                    };
                    vouchers.push(line_dict);
                }
            }
            res.vouchers = vouchers;
            return res;
        },
    });

    var VoucherGenerateButton = screens.ActionButtonWidget.extend({
        template: 'VoucherGenerateButton',
        button_click: function () {
            var self = this;
            var voucher_type_lines = self.pos.vouchers_type;
            var order = self.pos.get_order();
            if (!order.get_client()) {
                return self.gui.show_popup('alert', {
                    title: _t('Warning'),
                    body: _t('Please select customer!'),
                });
            }
            this.gui.show_popup('popupVoucherGenerate', {
                'title': _t('Generate Voucher'),
                'list': voucher_type_lines,
                'confirm': function (voucher_type, amount) {
                    console.log(voucher_type, amount);
                    if (amount > 0 && voucher_type) {
                        var select_voucher = self.pos.voucher_type_by_id[
                            voucher_type];
                        if (select_voucher) {
                            var product = self.pos.db.get_product_by_id(
                                select_voucher.product_id[0]);
                            if (product) {
                                order.add_product(product, {
                                    price: amount,
                                    extras: {voucher_type_id:
                                        select_voucher.id},
                                });
                            }
                        }
                    }
                },
            });
        },
    });

    screens.define_action_button({
        'name': 'discount',
        'widget': VoucherGenerateButton,
        'condition': function () {
            return true;
        },
    });

    return {
        voucherListScreenWidget: voucherListScreenWidget,
        VoucherGenerateButton: VoucherGenerateButton,
    };

});
