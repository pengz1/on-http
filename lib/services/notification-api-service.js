// Copyright 2016, EMC, Inc.

'use strict';

var di = require('di');

module.exports = notificationApiServiceFactory;
di.annotate(notificationApiServiceFactory, new di.Provide('Http.Services.Api.Notification'));
di.annotate(notificationApiServiceFactory,
    new di.Inject(
        'Protocol.Events',
        'Protocol.Task',
        'TaskGraph.Store',
        'Logger',
        'Services.Waterline',
        'Errors',
        'Promise',
        '_'
    )
);

function notificationApiServiceFactory(
    eventsProtocol,
    taskProtocol,
    taskGraphStore,
    Logger,
    waterline,
    Errors,
    Promise,
    _
) {
    var logger = Logger.initialize(notificationApiServiceFactory);

    function notificationApiService() {
    }

    notificationApiService.prototype.postNotification = function(message) {
        var self = this;

        if (_.has(message, 'nodeId')) {
            return self.postNodeNotification(message);
        } else if (_.has(message, 'taskId') && _.has(message, 'progress')) {
            return self.postProgressEvent(message);
        }
        // This will be a broadcast notification if no id (like nodeId) is specified
        else {
            return self.postBroadcastNotification(message);
        }
    };

    notificationApiService.prototype.postNodeNotification = function(message) {

        return Promise.try(function() {
            if (!message.nodeId || !_.isString(message.nodeId)) {
                throw new Errors.BadRequestError('Invalid node ID in query or body');
            }
        })
        .then(function () {
            return waterline.nodes.needByIdentifier(message.nodeId);
        })
        .then(function (node) {
            if(!node) {
                throw new Errors.BadRequestError('Node not found');
            }
            return eventsProtocol.publishNodeNotification(message.nodeId, message);
        })
        .then(function () {
            return message;
        });
    };

    notificationApiService.prototype.postBroadcastNotification = function(message) {
        return eventsProtocol.publishBroadcastNotification(message)
        .then(function () {
            return message;
        });
    };

    notificationApiService.prototype.postProgressEvent = function(data) {
        var progressData, nodeId;
        //return waterline.taskdependencies.needByIdentifier(data.taskId)
        return waterline.taskdependencies.find({taskId: data.taskId})
        .then(function(task){
            //return waterline.graphobjects.needByIdentifier(task.graphId);
            return waterline.graphobjects.find({instanceId: task[0].graphId});
        })
        .then(function(graphObject){
            progressData = {
                graphId: graphObject[0].instanceId,
                progress: {
                    percentage: "na",
                    msg: data.progress.msg,
                },
                taskProgress: {
                    graphId: graphObject[0].instanceId, 
                    taskId: data.taskId,
                    taskName: graphObject[0].tasks[data.taskId].friendlyName,
                    progress: data.progress 
                }
            };
            nodeId = graphObject[0].node;
        })
        .then(function(){
            return eventsProtocol.publishProgressEvent(nodeId, progressData);
        })
        .then(function(){
            return taskGraphStore.updateGraphProgress(progressData);
        })
        .then(function(){
            return taskGraphStore.updateTaskProgress(progressData.taskProgress);
        });
    };

    return new notificationApiService();
}
