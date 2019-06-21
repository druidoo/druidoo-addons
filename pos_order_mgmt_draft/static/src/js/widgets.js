
odoo.define('pos_order_mgmt_draft.widgets', function (require) {
    "use strict";

    var core = require('web.core');
    var _t = core._t;
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var chrome = require('point_of_sale.chrome');
    var pos = require('point_of_sale.models');

    var pos_mgmt = require('pos_order_mgmt.widgets');

    var QWeb = core.qweb;
    var ScreenWidget = screens.ScreenWidget;
    var DomCache = screens.DomCache;

    pos_mgmt.OrderListScreenWidget.include({

    	init: function(parent, options) {
    		var self = this;
    		this._super(parent, options);
    		this.search_type_filter = 'done';
    	},

    	show: function() {
    		var self = this;
    		this._super();
            this.clear_search();
    		this.$('.order-type-selector .button').on('click', function() {
    			self.search_type_filter = $(this).data('filter');
                self.perform_search();
    		})
    	},

    	perform_search: function() {
    		var self = this;
    		if (self.search_type_filter == 'done') { return this._super(); }
    		else if (self.search_type_filter == 'draft') {
    			return this.search_draft_orders(self.search_query)
    				.done(function() { self.render_list(); });
    		}
    	},

    	search_draft_orders: function(query) {
            var self = this;
            return this._rpc({
                model: 'pos.order',
                //method: 'search_draft_orders_for_pos',
                method: 'search_draft_orders_for_pos',
                args: [query || '', this.pos.pos_session.id],
            }).then(function (result) {
                self.orders = result;
            }).fail(function (error, event) {
                if (parseInt(error.code, 10) === 200) {
                    // Business Logic Error, not a connection problem
                    self.gui.show_popup(
                        'error-traceback', {
                            'title': error.data.message,
                            'body': error.data.debug,
                        }
                    );
                } else {
                    self.gui.show_popup('error', {
                        'title': _t('Connection error'),
                        'body': _t('Can not execute this action because the POS is currently offline'),
                    });
                }
                event.preventDefault();
            });
        },

        render_list: function() {
        	var self = this;
        	this._super();
            this.$('.order-list-open').off('click');
            this.$('.order-list-open').click(function(event) {
                self.order_list_actions(event, 'open');
            });
            // Update filter button status
            this.$('.order-type-selector .button').each(function(i, el) {
                var filter = $(el).data('filter');
                if (filter == self.search_type_filter) { 
                    $(el).addClass('active');
                } else { 
                    $(el).removeClass('active');
                }
            });
        },

        action_open: function(order_data) {
        	var order = this.load_order_from_data(order_data);
            if (!order) { return false; }
            // Restore the previous name
            order.name = order_data.pos_reference || order_data.name;
            order.odoo_id = order_data.id;
            order.trigger('change');
			this.pos.get('orders').add(order);
            this.pos.set('selectedOrder', order);
            return order;
        },

        action_print: function(order_data) {
            /* In case of draft orders, we print the pos.order report */
            if (order_data.state == 'draft') {
                return this.pos.chrome.do_action('pos_order_mgmt_draft.pos_order_report', {
                    additional_context: { active_ids: [order_data.id] }
                });
            } else {
                this._super(order_data);
            }
        },

        load_order_from_data: function(order_data) {
            var order = this._super(order_data);
            order.state = order_data.state;
            order.trigger('change');
            return order;
        },

    });


    screens.ActionpadWidget.include({

        renderElement: function() {
            var self = this;
            this._super();
            this.$('.save-draft').click(function() {
                var order = self.pos.get_order();
                if (order.is_empty()) return false;

                self.pos.gui.show_popup('confirm', {
                    title: _t('Save Order?'),
                    body: _t(
                        'The order will be saved as quotation.\r\n' +
                        'If it has already been saved, the quotation will be updated.\r\n' +
                        '\r\nAre you sure?'),
                    confirm: function() {
                        var args = [order.export_as_JSON()];
                        return self._rpc({
                            model: 'pos.order',
                            method: 'create_draft_from_ui',
                            args: args,
                        }).then(function (result) {
                            order.odoo_id = result;
                            order.trigger('change');
                            self.pos.chrome.do_action('pos_order_mgmt_draft.pos_order_report', {
                                additional_context: { active_ids: [order.odoo_id] }
                            });
                            order.destroy();
                        }).fail(function (error, event) {
                            if (parseInt(error.code, 10) === 200) {
                                // Business Logic Error, not a connection problem
                                self.gui.show_popup(
                                    'error-traceback', {
                                        'title': error.data.message,
                                        'body': error.data.debug,
                                    }
                                );
                            } else {
                                self.gui.show_popup('error', {
                                    'title': _t('Connection error'),
                                    'body': _t('Can not execute this action because the POS is currently offline'),
                                });
                            }
                            event.preventDefault();
                        });
                    }
                });
            });
        },

    });

})