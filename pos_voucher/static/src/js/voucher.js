odoo.define('pos_voucher.voucher_generate', function (require) {
"use strict";

var core = require('web.core');
var screens = require('point_of_sale.screens');
var _t = core._t;

var VoucherGenerateButton = screens.ActionButtonWidget.extend({
    template: 'VoucherGenerateButton',
    button_click: function(){
        var self = this;
        var voucher_type_lines = self.pos.vouchers_type;
        var order    = self.pos.get_order();
        if(!order.get_client()){
            return self.gui.show_popup('alert', {
                        title: _t('Warning'),
                        body: _t('Please select customer!'),
            });
        }
        this.gui.show_popup('popupVoucherGenerate',{
            'title': _t('Generate Voucher'),
            'list': voucher_type_lines,
        });
    },
});

screens.define_action_button({
    'name': 'discount',
    'widget': VoucherGenerateButton,
    'condition': function(){
        return true;
    },
});

return {
    VoucherGenerateButton: VoucherGenerateButton,
}

});
