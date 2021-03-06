;(function (define) {

define([
    'jquery',
    'backbone',
    'counter_icon_model',
    'notification_pane_view',
    'text!notification_icon_template'
], function ($, Backbone, CounterIconModel, NotificationPaneView, NotifcationIconUnderscoreTemplate) {
    'use strict';

    return Backbone.View.extend({
        initialize: function(options){
            this.options = options;
            this.endpoints = options.endpoints;
            this.view_templates = options.view_templates;

            /* initialize the model using the API endpoint URL that was passed into us */
            this.model = new CounterIconModel();
            this.model.url = this.endpoints.unread_notification_count;

            /* re-render if the model changes */
            this.listenTo(this.model,'change', this.modelChanged);

            /* make the async call to the backend REST API */
            /* after it loads, the listenTo event will file and */
            /* will call into the rendering */
            this.model.fetch();
        },

        events: {
            'click .edx-notifications-icon': 'showPane'
        },

        /* cached notifications pane view */
        notification_pane: null,

        template: null,

        modelChanged: function() {
            this.render();
        },

        render: function () {

            if (!this.template)
                this.template = _.template(NotifcationIconUnderscoreTemplate);

            this.$el.html(this.template(
                    this.model.toJSON()
                )
            );
       },

       showPane: function() {
            if (!this.notification_pane) {

                this.notification_pane = new NotificationPaneView({
                    el: this.options.pane_el,
                    endpoints: this.endpoints,
                    view_templates: this.view_templates
                });
            } else {
                this.notification_pane.show();
            }
       }
    });
});
})(define || RequireJS.define);
