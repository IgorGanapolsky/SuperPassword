<<<<<<< HEAD
=======
import { Platform } from "react-native";
import "setimmediate";

if (Platform.OS === "web") {
  require("./src/polyfills").default;
}

>>>>>>> fix/dependency-compatibility
import { registerRootComponent } from "expo";
import App from "./App";

registerRootComponent(App);
