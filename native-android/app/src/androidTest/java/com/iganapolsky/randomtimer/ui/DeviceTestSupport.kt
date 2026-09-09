package com.iganapolsky.randomtimer.ui

import android.content.Intent
import androidx.compose.ui.test.hasContentDescription
import androidx.compose.ui.test.hasScrollAction
import androidx.compose.ui.test.junit4.AndroidComposeTestRule
import androidx.compose.ui.test.onAllNodesWithContentDescription
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performScrollToNode
import androidx.test.ext.junit.rules.ActivityScenarioRule
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.By
import androidx.test.uiautomator.UiDevice
import androidx.test.uiautomator.Until
import com.iganapolsky.randomtimer.MainActivity
import com.iganapolsky.randomtimer.service.TimerForegroundService

/** Shared helpers for slow GitHub Actions emulators (API 30–34, swiftshader). */
object DeviceTestSupport {
    const val SETUP_READY_TIMEOUT_MS = 30_000L
    const val LABEL_READY_TIMEOUT_MS = 45_000L
    const val NOTIFICATION_UI_TIMEOUT_MS = 15_000L

    private const val MIN_TIME_SLIDER = "Minimum time slider"

    /**
     * Stops the app process so the next MainActivity lands on setup.
     * Call only from @BeforeClass / @AfterClass, never from per-method @After —
     * force-stop kills the instrumentation process mid-suite.
     */
    fun forceStopApp() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        instrumentation.uiAutomation.executeShellCommand(
            "am force-stop com.iganapolsky.randomtimer",
        )
    }

    fun stopTimerService() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val stopIntent =
            Intent(context, TimerForegroundService::class.java).apply {
                action = TimerForegroundService.ACTION_STOP
            }
        context.startService(stopIntent)
    }

    /** Cold start once per test class (safe before instrumentation launches MainActivity). */
    fun prepareColdStart() {
        stopTimerService()
        forceStopApp()
    }

    /** Reset UI between test methods without killing the instrumentation process. */
    fun prepareNextTest(
        rule: AndroidComposeTestRule<ActivityScenarioRule<MainActivity>, MainActivity>,
    ) {
        stopTimerService()
        rule.activityRule.scenario.recreate()
        waitForSetupScreen(rule)
    }

    fun waitForSetupScreen(
        rule: AndroidComposeTestRule<ActivityScenarioRule<MainActivity>, MainActivity>,
        timeoutMillis: Long = SETUP_READY_TIMEOUT_MS,
    ) {
        rule.waitUntil(timeoutMillis = timeoutMillis) {
            rule.onAllNodesWithTag("start_timer", useUnmergedTree = true)
                .fetchSemanticsNodes()
                .isNotEmpty()
        }
        rule.waitForIdle()
    }

    /** Time range sliders live in setup [LazyColumn]; scroll once before slider/label work. */
    fun scrollToTimeRangeSliders(
        rule: AndroidComposeTestRule<ActivityScenarioRule<MainActivity>, MainActivity>,
    ) {
        rule.waitUntil(timeoutMillis = SETUP_READY_TIMEOUT_MS) {
            rule.onAllNodesWithContentDescription(MIN_TIME_SLIDER, useUnmergedTree = true)
                .fetchSemanticsNodes()
                .isNotEmpty()
        }
        rule.onNode(hasScrollAction())
            .performScrollToNode(hasContentDescription(MIN_TIME_SLIDER))
        rule.waitForIdle()
    }

    fun waitForLabel(
        rule: AndroidComposeTestRule<ActivityScenarioRule<MainActivity>, MainActivity>,
        text: String,
        timeoutMillis: Long = LABEL_READY_TIMEOUT_MS,
    ) {
        scrollToTimeRangeSliders(rule)
        rule.waitUntil(timeoutMillis = timeoutMillis) {
            rule.onAllNodesWithText(text, useUnmergedTree = true)
                .fetchSemanticsNodes()
                .isNotEmpty()
        }
        rule.onNodeWithText(text, useUnmergedTree = true)
            .performScrollTo()
            .assertExists()
    }

    fun clickPrimaryStart(
        rule: AndroidComposeTestRule<ActivityScenarioRule<MainActivity>, MainActivity>,
    ) {
        rule.onNodeWithTag("start_timer", useUnmergedTree = true).performClick()
    }

    /**
     * Clicks a notification action after re-querying the node. Notification rows refresh after
     * actions like "+5 Min", which invalidates cached [UiObject2] handles (StaleObjectException).
     */
    fun clickNotificationAction(
        device: UiDevice,
        label: String,
        timeoutMs: Long = NOTIFICATION_UI_TIMEOUT_MS,
    ) {
        val visible = device.wait(Until.findObject(By.text(label)), timeoutMs)
        requireNotNull(visible) { "'$label' should be visible in notification shade" }
        val fresh = device.wait(Until.findObject(By.text(label)), timeoutMs)
        requireNotNull(fresh) { "'$label' disappeared before click" }
        fresh.click()
    }
}
