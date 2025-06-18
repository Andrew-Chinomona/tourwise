Feature: Host adds a property

  Scenario: Complete 6-step form
    Given I am a logged-in host
    When I visit the add property page
    And I complete all 6 steps
    Then I should see my property on my listings page
