import org.gradle.api.tasks.testing.Test
import org.gradle.testing.jacoco.plugins.JacocoTaskExtension
import org.gradle.testing.jacoco.tasks.JacocoReport

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.hilt)
    alias(libs.plugins.ksp)
    alias(libs.plugins.google.services) apply false
    alias(libs.plugins.firebase.crashlytics.plugin) apply false
    alias(libs.plugins.firebase.perf.plugin) apply false
    jacoco
}

val hasGoogleServicesConfig =
    listOf(
        "google-services.json",
        "src/debug/google-services.json",
        "src/release/google-services.json",
    ).any { file(it).exists() }

val enableFirebasePlugins =
    providers.gradleProperty("enableFirebasePlugins")
        .map(String::toBoolean)
        .orElse(hasGoogleServicesConfig)
        .get()

if (enableFirebasePlugins) {
    apply(plugin = "com.google.gms.google-services")
    apply(plugin = "com.google.firebase.crashlytics")
    apply(plugin = "com.google.firebase.firebase-perf")
} else {
    logger.lifecycle("google-services.json not found; skipping Firebase Gradle plugins for local verification.")
}

val ciCompileSdk = providers.gradleProperty("ciCompileSdk").orNull?.toIntOrNull()
val ciTargetSdk = providers.gradleProperty("ciTargetSdk").orNull?.toIntOrNull()
val ciVersionCode = providers.gradleProperty("ciVersionCode").orNull?.toIntOrNull()

android {
    namespace = "com.iganapolsky.randomtimer"
    compileSdk = ciCompileSdk ?: 36

    defaultConfig {
        applicationId = "com.iganapolsky.randomtimer"
        minSdk = 26
        targetSdk = ciTargetSdk ?: 36
        versionCode = ciVersionCode ?: 1778679362
        versionName = "1.3.60"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        // PostHog Analytics - from gradle.properties or CI secret
        buildConfigField("String", "POSTHOG_API_KEY", "\"${System.getenv("POSTHOG_API_KEY") ?: project.findProperty("POSTHOG_API_KEY") ?: ""}\"")
        buildConfigField(
            "String",
            "PRO_AUDIO_MANIFEST_URL",
            "\"${project.findProperty("PRO_AUDIO_MANIFEST_URL") ?: "https://raw.githubusercontent.com/IgorGanapolsky/Random-Timer/develop/content/pro_audio/runtime/latest.json"}\"",
        )
        val admobAppId =
            System.getenv("ADMOB_APP_ID_ANDROID")
                ?: "ca-app-pub-5173650670360699~4427145410"
        val admobRewardedUnitId =
            System.getenv("ADMOB_REWARDED_UNIT_ID_ANDROID")
                ?: "ca-app-pub-5173650670360699/8693693481"
        buildConfigField("String", "ADMOB_APP_ID", "\"$admobAppId\"")
        buildConfigField("String", "ADMOB_REWARDED_UNIT_ID", "\"$admobRewardedUnitId\"")
        manifestPlaceholders["admobAppId"] = admobAppId
    }

    signingConfigs {
        create("release") {
            val keystorePath = System.getenv("KEYSTORE_PATH")
            if (keystorePath != null) {
                storeFile = file(keystorePath)
                storePassword = System.getenv("KEYSTORE_PASSWORD")
                keyAlias = System.getenv("KEY_ALIAS")
                keyPassword = System.getenv("KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = false
            signingConfig = if (System.getenv("KEYSTORE_PATH") != null) {
                signingConfigs.getByName("release")
            } else {
                signingConfigs.getByName("debug")
            }
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        debug {
            isMinifyEnabled = false
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
    testOptions {
        unitTests {
            isIncludeAndroidResources = true
            isReturnDefaultValues = true
            // Robolectric 4.16 + SDK 36 requires JDK 21 and --add-opens (robolectric.org/getting-started).
            all {
                it.jvmArgs(
                    "--add-opens=java.base/java.lang=ALL-UNNAMED",
                    "--add-opens=java.base/java.util=ALL-UNNAMED",
                    "--add-opens=java.base/java.io=ALL-UNNAMED",
                    "--add-opens=java.base/java.net=ALL-UNNAMED",
                    "--add-opens=java.base/java.security=ALL-UNNAMED",
                    "--add-opens=java.base/java.text=ALL-UNNAMED",
                    "--add-opens=java.base/jdk.internal.access=ALL-UNNAMED",
                    "--add-opens=java.desktop/java.awt.font=ALL-UNNAMED",
                    "--add-opens=jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED",
                )
            }
        }
    }
    lint {
        // Work around upstream Compose lint detector crash:
        // IncompatibleClassChangeError in FrequentlyChangingValueDetector.
        // Keep lint enabled for all other checks.
        disable += "FrequentlyChangingValue"
        disable += "RememberInComposition"
        disable += "NullSafeMutableLiveData"
        disable += "AutoboxingStateCreation"
    }
}

dependencies {
    // Core Android
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.activity.compose)

    // Compose
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)
    implementation(libs.androidx.compose.material.icons.extended)
    implementation(libs.androidx.navigation.compose)

    // Dependency Injection
    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)
    implementation(libs.hilt.navigation.compose)

    // Data
    implementation(libs.androidx.datastore.preferences)

    // Coroutines
    implementation(libs.kotlinx.coroutines.core)
    implementation(libs.kotlinx.coroutines.android)

    // Analytics
    implementation(libs.posthog)

    // In-App Review
    implementation(libs.play.review)

    // In-App Update
    implementation(libs.play.update)

    // In-App Billing
    implementation(libs.play.billing)

    // AdMob (rewarded ads; gated by PostHog flag at runtime)
    implementation(libs.play.services.ads)

    // WorkManager
    implementation(libs.androidx.work.runtime)

    // Firebase
    implementation(platform(libs.firebase.bom))
    implementation(libs.firebase.crashlytics)
    implementation(libs.firebase.analytics)
    implementation(libs.firebase.perf)

    // Media Session (Bluetooth/Android Auto alarm dismiss)
    implementation(libs.androidx.media)

    // Testing
    testImplementation(libs.junit)
    testImplementation(libs.mockk)
    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(libs.turbine)
    testImplementation(libs.truth)
    testImplementation(libs.org.json)
    testImplementation(libs.androidx.test.core)
    testImplementation(libs.androidx.work.testing)
    testImplementation(libs.robolectric)

    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.test.core)
    androidTestImplementation(libs.androidx.test.rules)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(libs.androidx.test.uiautomator)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.ui.test.junit4)

    debugImplementation(libs.androidx.ui.tooling)
    debugImplementation(libs.androidx.ui.test.manifest)
}

jacoco {
    toolVersion = "0.8.12"
}

tasks.withType<Test>().configureEach {
    extensions.configure(JacocoTaskExtension::class.java) {
        isIncludeNoLocationClasses = true
        excludes = listOf("jdk.internal.*")
    }
}

tasks.register<JacocoReport>("jacocoDebugUnitTestReport") {
    dependsOn("testDebugUnitTest")

    reports {
        xml.required.set(true)
        html.required.set(true)
        csv.required.set(false)
    }

    val excludes = listOf(
        "**/R.class",
        "**/R$*.class",
        "**/BuildConfig.*",
        "**/Manifest*.*",
        "**/*Test*.*",
        "android/**/*.*",
        "**/*\$Lambda$*.*",
        "**/*\$inlined$*.*",
    )

    val buildDirFile = layout.buildDirectory.get().asFile
    val kotlinClasses = fileTree(buildDirFile.resolve("tmp/kotlin-classes/debug")) { exclude(excludes) }
    val javaClasses = fileTree(buildDirFile.resolve("intermediates/javac/debug/classes")) { exclude(excludes) }

    classDirectories.setFrom(files(kotlinClasses, javaClasses))
    sourceDirectories.setFrom(files("src/main/java", "src/main/kotlin"))
    executionData.setFrom(
        fileTree(buildDirFile) {
            include("jacoco/testDebugUnitTest.exec")
            include("outputs/unit_test_code_coverage/debugUnitTest/testDebugUnitTest.exec")
        }
    )
}
