odoo.define('pos_voucher.popups', function (require) {
"use strict";

var PopupWidget = require('point_of_sale.popups');
var gui = require('point_of_sale.gui');
var core = require('web.core');
var QWeb = core.qweb;
var _t = core._t;

var popupVoucherGenerate = PopupWidget.extend({
    template: 'popupVoucherGenerate',
    init: function (parent, options) {
        this._super(parent, options);
    },
    show: function (options) {
        var self = this;
        this._super(options);
        this.$(".cancel").click(function (e) {
            self.pos.gui.close_popup();
        });
        this.$('.input_form').focus();
        this.list = options.list || [];
    },
    renderElement: function () {
        var self = this;
        this._super();
        this.$('.cancel').click(function () {
            self.gui.close_popup();
        });
        this.$('.confirm').click(function () {
            var voucher_amount = $('#voucher_amount').val();
            var voucher_type_selection = $('#voucher_type_selection').val();
            var order    = self.pos.get_order();
            if (voucher_amount > 0 && voucher_type_selection){
                var select_voucher = self.pos.voucher_type_by_id[voucher_type_selection];
                if (select_voucher){
                    var product  = self.pos.db.get_product_by_id(select_voucher['product_id'][0]);
                    if (product){
                        order.add_product(product, {
                            price: voucher_amount,
                            extras: { voucher_type_id: select_voucher.id},
                        });
                    }
                }
            }
        })
    }
});

gui.define_popup({name: 'popupVoucherGenerate', widget: popupVoucherGenerate});


var popupAlertInput = PopupWidget.extend({
    template: 'alert_input',
    show: function (options) {
        options = options || {};
        this._super(options);
        this.renderElement();
        this.$('input').focus();
    },
    click_confirm: function () {
        var value = this.$('input').val();
        this.gui.close_popup();
        if (this.options.confirm) {
            this.options.confirm.call(this, value);
        }
    },
});

gui.define_popup({name: 'alert_input', widget: popupAlertInput});

return {
    popupVoucherGenerate: popupVoucherGenerate,
    popupAlertInput: popupAlertInput,
}


});