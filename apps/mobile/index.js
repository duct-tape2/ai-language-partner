import { registerRootComponent } from 'expo';
import App from './App';

// Registers App as the root component for both native (Expo Go / dev build)
// and web (react-native-web) targets. Version-proof entry point.
registerRootComponent(App);
