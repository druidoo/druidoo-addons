odoo.define('pos_voucher.popups', function (require) {
    "use strict";

    var PopupWidget = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    var core = require('web.core');
    var _t = core._t;


    var popupVoucherGenerate = PopupWidget.extend({
        template: 'popupVoucherGenerate',
        show: function (options) {
            var options_local = options || {};
            this._super(options_local);
            this.inputbuffer = String(options_local.value || '');
            this.decimal_separator = _t.database.parameters.decimal_point;
            this.renderElement();
            this.firstinput = true;
            this.list = options_local.list || [];
        },
        click_numpad: function (event) {
            var newbuf = this.gui.numpad_input(
                this.inputbuffer,
                $(event.target).data('action'),
                {'firstinput': this.firstinput});
            this.firstinput = newbuf.length === 0;
            if (newbuf !== this.inputbuffer) {
                this.inputbuffer = newbuf;
                this.$('.value').text(this.inputbuffer);
            }
        },
        click_confirm: function () {
            this.gui.close_popup();
            if (this.options.confirm) {
                this.options.confirm.call(
                    this,
                    $('#voucher_type_selection').val(),
                    parseFloat(this.inputbuffer.replace(',', '.'))
                );
            }
        },
    });
    gui.define_popup({name: 'popupVoucherGenerate',
        widget: popupVoucherGenerate});
    var popupAlertInput = PopupWidget.extend({
        template: 'alert_input',
        show: function (options) {
            var options_local = options || {};
            this._super(options_local);
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
    };
});
