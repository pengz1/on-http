// Copyright 2016, EMC, Inc.

'use strict';

var injector = require('../../../index.js').injector;
var controller = injector.get('Http.Services.Swagger').controller;
var config = injector.get('Http.Services.Api.Config');

var configGet = controller(function(req) {
    return config.configGetAll(req.query);
});

var configPatch = controller(function(req) {
    return config.configSet(req.body);
});

var configHooksGetAll = controller(function() {
    return config.configGetAllHooks();
});

var configHooksPost = controller({success: 201}, function(req) {
    return config.configCreateHooks(req.body);
});

module.exports = {
    configGet: configGet,
    configPatch: configPatch,
    configHooksGetAll: configHooksGetAll,
    configHooksPost: configHooksPost
};

