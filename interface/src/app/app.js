angular.module( 'adage', [
  'templates-app',
  'templates-common',
  'adage.home',
  'adage.about',
  'adage.analyze',
  'adage.download',
  'adage.tribe_auth.user',
  'ui.router',
  'ngResource'
])

.config( function myAppConfig ( $stateProvider, $urlRouterProvider ) {
  //$urlRouterProvider.otherwise( '/home' );
})

// This configuration is required for all REST calls to the back end
.config(['$resourceProvider', function($resourceProvider) {
  // Don't strip trailing slashes from calculated URLs
  $resourceProvider.defaults.stripTrailingSlashes = false;
}])

.run( function run ( $state, $location ) {

    // Will only redirect if there is no state AND the url is not a
    // route for tribe_client
    String.prototype.startsWith = function(prefix) {
        return this.slice(0, prefix.length) == prefix;
    };

    if ($state['current']['name'] === '') {
      if (window.location.pathname.startsWith('/tribe_client')) {
      }
      else {
          $state.go('home');
      }
    }


})

.controller( 'AppCtrl', function AppCtrl ( $scope, $location, UserFactory ) {

  $scope.$on('$stateChangeSuccess', function(event, toState, toParams, fromState, fromParams){
    if ( angular.isDefined( toState.data.pageTitle ) ) {
      $scope.pageTitle = toState.data.pageTitle + ' | adage' ;
    }
  });

  UserFactory.getPromise().$promise.then( function() {
        $scope.user = UserFactory.getUser();
  });

})

;
