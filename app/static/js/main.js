angular.module('serverApp', [])
    .controller('UsersController', ['$scope', '$interval', '$http', function($scope, $interval, $http) {
        $scope.allied_users = []
        $scope.axis_users = []
        $scope.game_state = {}
        $scope.interval
        $scope.server_down = false
        $scope.update_time = Date()

        $scope.kick = function(eugen_id) {
            console.log("kick")
            $http.get("users/kick/".concat(eugen_id))
            .then(function (response) {
                console.log(response)
                alert(response.data.message);
                $scope.reloadUsers()
            });
        };

        $scope.ban = function(eugen_id) {
            console.log("ban")
            $http.get("users/ban/".concat(eugen_id))
            .then(function (response) {
                console.log(response)
                alert(response.data.message);
                $scope.reloadUsers()
                
            });
        };

        $scope.swap = function(eugen_id) {
            $http.get("users/swap/".concat(eugen_id))
            .then(function (response) {
                console.log(response)
                alert(response.data.message);
                $scope.reloadUsers()
            });
        };

        $scope.reloadState = function() {
            
            $http.get("users/current")
            .then(function success(response) {
                $scope.allied_users = response.data.allied_users;
                $scope.axis_users = response.data.axis_users;
                $scope.server_down = false
            }, function error(response) {
                $scope.server_down = true
            });
            $http.get("game/state")
            .then(function success(response) {
                $scope.game_state = response.data;
                $scope.update_time = Date()
                $scope.server_down = false
            }, function error(response) {
                $scope.update_time = Date()
                $scope.server_down = true
            });
        }

        $scope.reloadState();
        $scope.interval = $interval( function(){ $scope.reloadState(); }, 5000);
    }]);