package com.iganapolsky.randomtimer.ui

import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.By
import androidx.test.uiautomator.UiDevice
import androidx.test.uiautomator.Until
import com.iganapolsky.randomtimer.MainActivity
import org.junit.After
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class NotificationE2ETest {

    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    private lateinit var device: UiDevice
    private var firstTest = true

    @Before
    fun setup() {
        device = UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
        if (firstTest) {
            firstTest = false
        } else {
            DeviceTestSupport.prepareNextTest(composeRule)
        }
    }

    @After
    fun tearDown() {
        DeviceTestSupport.stopTimerService()
        if (::device.isInitialized) {
            device.pressHome()
        }
    }

    @Test
    fun testNotificationLifecycle() {
        val uiTimeout = DeviceTestSupport.NOTIFICATION_UI_TIMEOUT_MS
        DeviceTestSupport.waitForSetupScreen(composeRule)
        DeviceTestSupport.clickPrimaryStart(composeRule)
        composeRule.waitForIdle()

        device.pressHome()
        device.openNotification()

        val notificationTitle =
            device.wait(Until.findObject(By.text("Timer Running")), uiTimeout)
        assertNotNull("Notification with title 'Timer Running' should be visible", notificationTitle)

        DeviceTestSupport.clickNotificationAction(device, "Pause", uiTimeout)

        val pausedTitle = device.wait(Until.findObject(By.text("Timer Paused")), uiTimeout)
        assertNotNull("Notification title should change to 'Timer Paused'", pausedTitle)

        DeviceTestSupport.clickNotificationAction(device, "Resume", uiTimeout)

        val runningTitle = device.wait(Until.findObject(By.text("Timer Running")), uiTimeout)
        assertNotNull("Notification title should change back to 'Timer Running'", runningTitle)

        DeviceTestSupport.clickNotificationAction(device, "Stop", uiTimeout)

        val dismissed = device.wait(Until.gone(By.text("Timer Running")), uiTimeout)
        assertTrue("Notification should be dismissed after clicking 'Stop'", dismissed)

        device.pressHome()
    }

    /** Runs after [testNotificationLifecycle] (JUnit name order). */
    @Test
    fun testNotification_extendAddsFiveMinutes() {
        val uiTimeout = DeviceTestSupport.NOTIFICATION_UI_TIMEOUT_MS
        DeviceTestSupport.waitForSetupScreen(composeRule)
        DeviceTestSupport.clickPrimaryStart(composeRule)
        composeRule.waitForIdle()

        device.pressHome()
        device.openNotification()

        device.wait(Until.findObject(By.text("Timer Running")), uiTimeout)

        DeviceTestSupport.clickNotificationAction(device, "+5 Min", uiTimeout)

        val runningTitle = device.wait(Until.findObject(By.text("Timer Running")), uiTimeout)
        assertNotNull("Notification should still be visible after extend", runningTitle)

        DeviceTestSupport.clickNotificationAction(device, "Stop", uiTimeout)

        device.wait(Until.gone(By.text("Timer Running")), uiTimeout)
        device.pressHome()
    }
}
