odoo.define('web_calendar_color_field.Calendar', function (require) {
"use strict";

var core = require('web.core');
var fieldUtils = require('web.field_utils');
var CalendarView = require('web.CalendarView');
var CalendarModel = require('web.CalendarModel');
var CalendarRenderer = require('web.CalendarRenderer');
var _t = core._t;

CalendarView.include({
    /**
     * When using a one2many relation field as color,
     * color_field will allow to select a field to specify
     * the exact color of the event in the calendar.
     */
    init: function(viewInfo, params) {
        this._super.apply(this, arguments);
        // This should actually be like this:
        // this.loadParams.fieldColorRelated = this.arch.attrs.color_field;
        // But there's no way to extend the rng files used for view validations,
        // so it's impossible to add a color_field attribute on the calendar views.
        // It sucks but that's the way it works right now. Hardcoding it to color then
        this.loadParams.fieldColorRelated = 'color';
    },
});

CalendarModel.include({

    /**
     * Overload to capture the fieldColorRelated parameter
     */
    load: function(params) {
        this.fieldColorRelated = params.fieldColorRelated;
        return this._super.apply(this, arguments);
    },

    /**
     * Prefetchs the color index field from the fieldColor relation
     *
     * @private
     * @param {any} events
     * @returns {Deferred}
     */
    _prefetchColorRelatedFields: function (events) {
        var self = this;
        if (this.fieldColor && this.fieldColorRelated && this.fields[this.fieldColor].type == 'many2one') {
            var done = $.Deferred();
            var ids = _.uniq(_.map(events, function(event) {
                if (_.isArray(event[self.fieldColor])) {
                    return event[self.fieldColor][0]
                } else {
                    return false;
                }
            }));
            this._rpc({
                model: this.fields[self.fieldColor].relation,
                method: 'search_read',
                context: this.data.context,
                fields: ['id', this.fieldColorRelated],
                domain: [['id', 'in', ids]],
            })
            .then(function(relData) {
                _.each(events, function(event) {
                    if (_.isArray(event[self.fieldColor])) {
                        var relObj = _.find(relData, function(d) { return d.id == event[self.fieldColor][0]; });
                        if (relObj && relObj[self.fieldColorRelated]) {
                            event[self.fieldColor].push(relObj[self.fieldColorRelated]);
                        }
                    }
                });
                done.resolve();
            });
            return done;
        } else {
            return $.when();
        }
    },

    /**
    * Overload to prefetch color related fields, if needed
    */
    _loadCalendar: function () {
        var self = this;
        this.data.fullWidth = this.call('local_storage', 'getItem', 'calendar_fullWidth') === true;
        this.data.fc_options = this._getFullCalendarOptions();
        var defs = _.map(this.data.filters, this._loadFilter.bind(this));
        return $.when.apply($, defs).then(function () {
            return self._rpc({
                    model: self.modelName,
                    method: 'search_read',
                    context: self.data.context,
                    fields: self.fieldNames,
                    domain: self.data.domain.concat(self._getRangeDomain()).concat(self._getFilterDomain())
            })
            .then(function (events) {
                self._parseServerData(events);
                self.data.data = _.map(events, self._recordToCalendarEvent.bind(self));
                var done = $.Deferred();
                self._prefetchColorRelatedFields(events).then(function() {
                    $.when(
                        self._loadColors(self.data, self.data.data),
                        self._loadRecordsToFilters(self.data, self.data.data)
                    ).then(function() {
                        done.resolve();
                    })
                })
                return done;
            });
        });
    },


    /**
     * Overload to handle custom colorIndex
     */
    _loadColors: function (element, events) {
        if (this.fieldColor) {
            var fieldName = this.fieldColor;
            _.each(events, function (event) {
                var value = event.record[fieldName];
                event.color_index = _.isArray(value) ? value[0] : value;
                if (_.isArray(value) && value.length == 3) { event.color_index = String(value[2]); }
            });
            this.model_color = this.fields[fieldName].relation || element.model;
        }
        return $.Deferred().resolve();
    },

    /**
     * Overload to handle custom colorIndex
     */
    _loadRecordsToFilters: function (element, events) {
        var self = this;
        var new_filters = {};
        var to_read = {};

        _.each(this.data.filters, function (filter, fieldName) {
            var field = self.fields[fieldName];

            new_filters[fieldName] = filter;
            if (filter.write_model) {
                if (field.relation === self.model_color) {
                    _.each(filter.filters, function (f) {
                        f.color_index = f.value;
                    });
                }
                return;
            }

            _.each(filter.filters, function (filter) {
                filter.display = !filter.active;
            });

            var fs = [];
            var undefined_fs = [];
            _.each(events, function (event) {
                var data =  event.record[fieldName];
                if (!_.contains(['many2many', 'one2many'], field.type)) {
                    data = [data];
                } else {
                    to_read[field.relation] = (to_read[field.relation] || []).concat(data);
                }
                _.each(data, function (_value) {
                    var value = _.isArray(_value) ? _value[0] : _value;
                    var color_val = value;
                    if (_.isArray(_value) && _value.length == 3) { color_val = String(_value[2]); }
                    var f = {
                        'color_index': self.model_color === (field.relation || element.model) ? color_val : false,
                        'value': value,
                        'label': fieldUtils.format[field.type](_value, field) || _t("Undefined"),
                        'avatar_model': field.relation || element.model,
                    };
                    // if field used as color does not have value then push filter in undefined_fs,
                    // such filters should come last in filter list with Undefined string, later merge it with fs
                    value ? fs.push(f) : undefined_fs.push(f);
                });
            });
            _.each(_.union(fs, undefined_fs), function (f) {
                var f1 = _.findWhere(filter.filters, f);
                if (f1) {
                    f1.display = true;
                } else {
                    f.display = f.active = true;
                    filter.filters.push(f);
                }
            });
        });

        var defs = [];
        _.each(to_read, function (ids, model) {
            defs.push(self._rpc({
                    model: model,
                    method: 'name_get',
                    args: [_.uniq(ids)],
                })
                .then(function (res) {
                    to_read[model] = _.object(res);
                }));
        });
        return $.when.apply($, defs).then(function () {
            _.each(self.data.filters, function (filter) {
                if (filter.write_model) {
                    return;
                }
                if (filter.filters.length && (filter.filters[0].avatar_model in to_read)) {
                    _.each(filter.filters, function (f) {
                        f.label = to_read[f.avatar_model][f.value];
                    });
                }
            });
        });
    },

});

CalendarRenderer.include({
    /**
     * Overload to allow using custom color index
     * If key is a numeric string, we use it's value as color index
     */
    getColor: function (key) {
        // check if the key is a color index
        // we consider color index a string number
        if (typeof key === 'string' && key == Number(key)) {
            return Number(key);
        }
        return this._super.apply(this, arguments);
    },

});


});
