// Web entry point

import { AppRegistry } from 'react-native';
import { App } from './App';

AppRegistry.registerComponent('SuperPassword', () => App);
AppRegistry.runApplication('SuperPassword', {
  rootTag: document.getElementById('root'),
  initialProps: {},
});

// Handle web-specific setup
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/service-worker.js')
      .then((registration) => {
        console.log('SW registered:', registration);
      })
      .catch((error) => {
        console.log('SW registration failed:', error);
      });
  });
}
