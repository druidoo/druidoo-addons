/* Copyright 2019 Druidoo - Iván Todorovich
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */
   
odoo.define('pos_order_mgmt_draft_downpayment.screens', function (require) {
"use strict";

var core = require('web.core');
var gui = require('point_of_sale.gui');
var models = require('point_of_sale.models');
var screens = require('point_of_sale.screens');
var draft_screens = require('pos_order_mgmt_draft.screens');

var QWeb = core.qweb;
var _t = core._t;

var PaymentScreenWidget = screens.PaymentScreenWidget;
var DraftOrderScreenWidget = draft_screens.DraftOrderScreenWidget;


DraftOrderScreenWidget.include({

    click_advance_payment: function() {
        var self = this;
        var order = this.pos.get_order();
        // Save order first
        var saved = this.save_draft_order();
        saved.done(function() {
            self.gui.show_popup('number', {
                'title': _t('Advance Payment'),
                'body': _t('Enter the advance payment amount'),
                confirm: function(val) {
                    self.create_advance_payment(order, val);
                },
            });
        });
    },

    create_advance_payment: function(order, amount) {
        // Creates an advance payment
        var self = this;

        if (amount <= 0) {
            self.gui.show_popup('error', {
                'title': _t('Advance payment amount'),
                'body': _t('The Advance Payment has to be larger than 0.'),
            });
            return false;
        }

        if (amount >= order.get_total_with_tax()) {
            self.gui.show_popup('error', {
                'title': _t('Advance payment amount'),
                'body': _t('The Advance Payment cannot be larger than the order amount'),
            });
            return false;
        }

        if (!this.pos.config.deposit_product_id) {
            self.gui.show_popup('error', {
                'title': _t('Missing Deposit Product'),
                'body': _t('There\'s no deposit product in the POS Configuration'),
            });
            return false;
        }

        var deposit_product_id = this.pos.db.get_product_by_id(
            this.pos.config.deposit_product_id[0]);

        if (!deposit_product_id) {
            self.gui.show_popup('error', {
                'title': _t('No Advance Payment Product'),
                'body': _t(
                    'There\'s a product in the config, but it\'s not loaded ' +
                    'on the POS. Try refreshing the browser. ' +
                    'Also, make sure the deposit product is available on the POS'
                ),
            });
            return false;
        }

        // Create the advance payment order
        var deposit_order = new models.Order({},{
            pos: this.pos,
            temporary: true,
        });

        deposit_order.downpayment_order_id = order.odoo_id;
        deposit_order.set_client(order.get_client());
        deposit_order.add_product(deposit_product_id, {quantity: 1, price: amount});
        this.pos.get('orders').add(deposit_order);
        this.pos.set('selectedOrder', deposit_order);
        this.pos.gui.show_screen('payment');

        // Add advance payment line to current order, once the deposit is validated
        this.pos.get_order().on('validated', function() {
            order.assert_editable();
            /*  The following lines avoid raising a 'parentNode' error that occurs
                when adding lines in a not selected order.
                We have to check if the order is still on the pos before selecting it back,
                because depending on the IoT Box settings the screen receipt could've been
                closed and the order removed automatically. */
            self.pos.set('selectedOrder', order);
            order.add_product(deposit_product_id, {quantity: 1, price: (-amount)})
            if (self.pos.get('orders').contains(this)) {
                self.pos.set('selectedOrder', this);
            }
            self.push_draft_order(order);
        });

    },

    renderElement: function() {
        var self = this;
        this._super();
        this.$('.js_advance_payment').click(function() {
            self.click_advance_payment();
        });
    },

    show: function(){
        this.order_changes();
        this._super();
    },

    order_is_valid: function() {
        var self = this;
        var order = this.pos.get_order();
        if (order.temporary) {
            this.gui.show_popup('error', {
                'title': _t('temporary order'),
                'body': _t('temporary orders can not be saved as draft'),
            });
            return false
        }
        return this._super();
    },
});

PaymentScreenWidget.include({
    finalize_validation: function() {
        var self = this;
        var order = this.pos.get_order();
        this._super();
        order.trigger('validated', order);
    }
});

screens.ActionpadWidget.include({
    renderElement: function() {
        var self = this;
        this._super();
    },
});

});
