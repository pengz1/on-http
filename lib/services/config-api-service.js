// Copyright 2016, EMC, Inc.

'use strict';

var di = require('di');

module.exports = configApiServiceFactory;
di.annotate(configApiServiceFactory, new di.Provide('Http.Services.Api.Config'));
di.annotate(configApiServiceFactory,
    new di.Inject(
        'Services.Configuration',
        'Logger',
        'uuid',
        '_'
    )
);
function configApiServiceFactory(
    configuration,
    Logger,
    uuid,
    _
) {
    var logger = Logger.initialize(configApiServiceFactory);
    function ConfigApiService() {
    }

    /**
     * Get server configuration
     * @return {Promise}
     */

    ConfigApiService.prototype.configGetAll = function () {
        // get the config

        return configuration.getAll();
    };

    /**
     * Set server configuration
     * @param {Object} [req] HTTP request
     * @param {Object} [res] HTTP response
     * @return {Promise}
     */

    ConfigApiService.prototype.configSet = function(config) {

        _.forOwn(config, function (value, key) {
            configuration.set(key, value);
        });

        return configuration.getAll();
    };

    /**
     * Get all hooks
     * @param {Object} [req] HTTP request
     * @param {Object} [res] HTTP response
     * @return {Promise}
     */

    ConfigApiService.prototype.configGetAllHooks = function() {
        return configuration.get('hooks', []);
    };

    /**
     * Create new hooks
     * @param {Object} [req] HTTP request
     * @param {Object} [res] HTTP response
     * @return
     */

    ConfigApiService.prototype.configCreateHooks = function(hooks) {
        var hooks = Array.isArray(hooks) ? hooks : [hooks];
        var existingHooks = configuration.get('hooks', []);
        hooks = _.map(hooks, function(hook){
            hook.id = uuid.v4();
        })
        if (_.isEmpty(existingHooks)){
            existingHooks = hooks;
        } else {
            _.forEach(hooks, function(hook){
                existingHooks = _addHookToExistingHooks(hook, existingHooks);
            })
        }

        configuration.set('hooks', existingHooks);
        return configuration.persist('hooks', existingHooks);
    };

    function _addHookToExistingHooks(hook, existingHooks){
        var isNewHook = true;

        _.forEach(existingHooks, function(value, key){
            if (hook.address !== value.address){
                continue;
            }
            if (_.isEqual(hook.filters, value.filters)) {
                logger.warning('Hooks already exists', {
                    newHook: hook,
                    existingHook: value
                });
            } else {
                value.filters = _.concat(hook.filters, value.filters);
                existingHooks[key].filters = _.uniqWith(value.filters, _.isEqual);
            }
            isNewHook = false;
            break;
        });

        if (isNewHook) {
            existingHooks.push(hook);
        }
        return existingHooks;
    }

    return new ConfigApiService();
}
