/* Copyright 2019 Druidoo - Iván Todorovich
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */
   
odoo.define('pos_order_mgmt_draft.screens', function (require) {
"use strict";

var core = require('web.core');
var gui = require('point_of_sale.gui');
var screens = require('point_of_sale.screens');
var models = require('point_of_sale.models');

var QWeb = core.qweb;
var ScreenWidget = screens.ScreenWidget;
var _t = core._t;


var DraftOrderScreenWidget = ScreenWidget.extend({
    template:      'DraftOrderScreenWidget',
    back_screen:   'product',

    init: function(parent, options) {
        var self = this;
        this._super(parent, options);

        this.pos.bind('change:selectedOrder',function(){
                this.renderElement();
                this.watch_order_changes();
            },this);
        this.watch_order_changes();

        this.pos.bind('change:selectedClient', function() {
            self.customer_changed();
        }, this);
    },

    // sets up listeners to watch for order changes
    watch_order_changes: function() {
        var self = this;
        var order = this.pos.get_order();
        if (!order) { return; }
        if(this.old_order){
            this.old_order.unbind(null,null,this);
        }
        order.bind('all',function(){
            self.order_changes();
        });
        this.old_order = order;
    },

    // called when the order is changed
    order_changes: function(){
        var self = this;
        var order = this.pos.get_order();
        if (!order) {
            return;
        } else if (order.odoo_id) {
            self.$('h1').html(order.name)
        }else{
            self.$('h1').html('New draft order')
        }
    },

    customer_changed: function() {
        var client = this.pos.get_client();
        this.$('.js_customer_name').text( client ? client.name : _t('Customer') ); 
    },

    click_set_customer: function(){
        this.gui.show_screen('clientlist');
    },

    click_print: function() {
        var self = this;
        var order = this.pos.get_order();
        var saved = this.save_draft_order().done(function() {
            self.pos.chrome.do_action('pos_order_mgmt_draft.pos_order_report', {
                additional_context: { active_ids: [order.odoo_id] }
            });
        });
    },

    click_send_mail: function() {
        var order = this.pos.get_order();
        var saved = this.save_draft_order({send_mail: order.to_send_mail});
    },

    click_back: function(){
        this.gui.show_screen('products');
    },

    click_next: function() {
        var self = this;
        var order = this.pos.get_order();
        var saved = this.save_draft_order().done(function() {
            // Remove order from localStorage and UI
            order.destroy();
        });
    },

    click_cancel: function() {
        var self = this;
        var order = this.pos.get_order();
        this.gui.show_popup('confirm',{
            'title': _t('Cancel the order'),
            'body': _t('Are you sure you want to cancel the order?'),
            confirm: function(){
                if (order.odoo_id) {
                    this._rpc({
                        model: 'pos.order',
                        method: 'action_pos_order_cancel',
                        args: [order.odoo_id],
                    }).then(function() {
                        order.destroy();
                    }).fail(function (error, event) {
                        if (parseInt(error.code, 10) === 200) {
                            // Business Logic Error, not a connection problem
                            self.gui.show_popup('error-traceback', {
                                'title': error.data.message,
                                'body': error.data.debug,
                            });
                        } else {
                            self.gui.show_popup('error', {
                                'title': _t('Connection error'),
                                'body': _t('Can not execute this action because the POS is currently offline'),
                            });
                        }
                        event.preventDefault();
                        done.reject(error);
                    });
                } else {
                    order.destroy();
                }
            },
        });
    },

    renderElement: function() {
        var self = this;
        this._super();
        this.$('.back').click(function(){
            self.click_back();
        });
        this.$('.next').click(function(){
            self.click_next();
        });
        this.$('.js_set_customer').click(function(){
            self.click_set_customer();
        });
        this.$('.js_print').click(function(){
            self.click_print();
        });
        this.$('.js_send_mail').click(function(){
            self.click_send_mail();
        });
        this.$('.js_cancel').click(function() {
            self.click_cancel();
        });
    },

    show: function(){
        this.order_changes();
        this._super();
    },

    order_is_valid: function() {
        var self = this;
        var order = this.pos.get_order();
        if (order.is_empty()) {
            this.gui.show_popup('error',{
                'title': _t('Empty Order'),
                'body':  _t('There must be at least one product in your order before it can be saved'),
            });
            return false;
        }
        if(!order.get_client()){
            this.gui.show_popup('confirm',{
                'title': _t('Please select the Customer'),
                'body': _t('You need to select the customer before you can save a quotation.'),
                confirm: function(){
                    self.gui.show_screen('clientlist');
                },
            });
            return false;
        }
        return true;
    },

    push_draft_order: function(order, options) {
        var self = this;
        var options = options || {};
        var done = new $.Deferred();
        this._rpc({
            model: 'pos.order',
            method: 'create_draft_from_ui',
            args: [order.export_as_JSON(), options],
        }).then(function (result) {
            order.odoo_id = result;
            order.trigger('change');
            done.resolve();
        }).fail(function (error, event) {
            if (parseInt(error.code, 10) === 200) {
                // Business Logic Error, not a connection problem
                self.gui.show_popup('error-traceback', {
                    'title': error.data.message,
                    'body': error.data.debug,
                });
            } else {
                self.gui.show_popup('error', {
                    'title': _t('Connection error'),
                    'body': _t('Can not execute this action because the POS is currently offline'),
                });
            }
            event.preventDefault();
            done.reject(error);
        });
        return done;
    },

    save_draft_order: function(options) {
        var self = this;
        var order = this.pos.get_order();
        if (this.order_is_valid()) {
            return this.push_draft_order(order, options);
        } else {
            var res = new $.Deferred();
            res.reject();
            return res;
        }
    },
});

gui.define_screen({name:'draftorder', widget: DraftOrderScreenWidget});

screens.ActionpadWidget.include({
    renderElement: function() {
        var self = this;
        this._super();
        this.$('.save-draft').click(function() {
            self.pos.gui.show_screen('draftorder');
        });
    },
});

return {
    DraftOrderScreenWidget: DraftOrderScreenWidget,
}

});
