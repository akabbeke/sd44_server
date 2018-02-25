angular.module('serverApp', [])
    .controller('UsersController', ['$scope', '$interval', '$http', function($scope, $interval, $http) {
        $scope.allied_users = []
        $scope.axis_users = []

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

        $scope.reloadUsers = function() {
            $http.get("users/current")
            .then(function (response) {
                console.log(response)
                $scope.allied_users = response.data.allied_users;
                $scope.axis_users = response.data.axis_users;
            });
        }

        $scope.reloadUsers()

        $interval( function(){ $scope.reloadUsers(); }, 30000);
    }]);