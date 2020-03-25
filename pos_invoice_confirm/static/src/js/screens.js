/* Copyright 2019 Druidoo - Iván Todorovich
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */
odoo.define('pos_invoice_confirm.screens', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');
    var PaymentScreenWidget = screens.PaymentScreenWidget;
    var core = require('web.core');
    var _t = core._t;

    PaymentScreenWidget.include({
        renderElement: function () {
            var self = this;
            this._super();
            this.$('#button_next').click(function () {
                var order = self.pos.get_order();
                if (self.pos.config.module_account &&
                    self.pos.config.iface_invoice_order_reminder &&
                    order.is_to_invoice() === false && order.get_client()) {
                    self.gui.show_popup('confirm', {
                        'title': _t('Invoice Reminder'),
                        'body': _t('This order will not be invoiced, are'+
                        ' you sure you want to continue?'),
                        confirm: function () {
                            self.validate_order();
                        },
                    });
                } else {
                    self.validate_order();
                }
            });
        },
        order_changes: function () {
            var self = this;
            this._super();
            var order = this.pos.get_order();
            if (!order) {
                return;
            } else if (order.is_paid()) {
                self.$('.next1').addClass('highlight');
            } else {
                self.$('.next1').removeClass('highlight');
            }
        },
    });

});
