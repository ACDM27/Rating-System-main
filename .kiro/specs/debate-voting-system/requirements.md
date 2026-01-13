# Requirements Document

## Introduction

Transform the existing AI course defense scoring system into a comprehensive debate competition voting system. The system will maintain the current UI design style and technical architecture while adapting the functionality to support debate competitions with judge scoring, audience voting, and real-time result display.

## Glossary

- **System**: The debate competition voting system
- **Admin**: Administrator with full system control via PC interface
- **Judge**: Evaluator who scores individual debaters via mobile interface
- **Audience**: Participants who vote for teams via mobile interface
- **Display_Screen**: Large screen showing real-time progress and results
- **Debater**: Individual participant in the debate competition
- **Team**: Group of debaters (Pro or Con side)
- **Swing_Vote**: The difference between pre-debate and post-debate votes

## Requirements

### Requirement 1: System Role Transformation

**User Story:** As a system administrator, I want to transform user roles from academic to debate context, so that the system supports debate competition workflows.

#### Acceptance Criteria

1. WHEN the system initializes, THE System SHALL support four user roles: Admin, Judge, Audience, and Display_Screen
2. WHEN a user logs in as Judge, THE System SHALL provide mobile-optimized scoring interface for individual debaters
3. WHEN a user logs in as Audience, THE System SHALL provide mobile-optimized voting interface for teams
4. WHEN a user accesses Display_Screen, THE System SHALL show real-time voting progress without revealing vote counts
5. THE System SHALL maintain existing UI design consistency across all transformed interfaces

### Requirement 2: Judge Scoring System

**User Story:** As a judge, I want to score individual debaters across multiple dimensions, so that I can evaluate their performance comprehensively.

#### Acceptance Criteria

1. WHEN a judge accesses the scoring interface, THE System SHALL display tabs for Pro and Con teams with accordion-style debater cards
2. WHEN a judge scores a debater, THE System SHALL validate scores against six dimensions: Language Expression (20), Logical Reasoning (20), Debate Skills (20), Quick Response (15), Overall Awareness (15), General Impression (10)
3. WHEN a judge enters an invalid score, THE System SHALL display range validation messages
4. WHEN a judge completes all scores, THE System SHALL enable submission with confirmation dialog
5. WHEN a judge submits scores, THE System SHALL prevent further modifications and calculate averages with two decimal precision

### Requirement 3: Audience Voting System

**User Story:** As an audience member, I want to vote for teams before and after the debate, so that I can express my opinion changes.

#### Acceptance Criteria

1. WHEN an audience member accesses voting interface, THE System SHALL display split-screen layout with Pro (red) and Con (blue) team sections
2. WHEN voting is enabled, THE System SHALL provide large touch-friendly buttons with minimum 60px height
3. WHEN an audience member votes, THE System SHALL record the vote and prevent duplicate voting for the same phase
4. WHEN an audience member submits a vote, THE System SHALL display loading overlay and confirmation message
5. THE System SHALL allow each audience member exactly two votes: one pre-debate and one post-debate

### Requirement 4: Swing Vote Calculation

**User Story:** As a system administrator, I want to calculate team victory based on vote swing, so that I can determine which team was more persuasive.

#### Acceptance Criteria

1. WHEN calculating team results, THE System SHALL compute swing vote as post-debate votes minus pre-debate votes for each team
2. WHEN comparing teams, THE System SHALL declare the team with higher swing vote as winner
3. WHEN swing votes are equal, THE System SHALL declare a tie
4. THE System SHALL store all vote calculations with timestamp precision
5. THE System SHALL display swing vote calculations in the final results

### Requirement 5: Individual Debater Ranking

**User Story:** As a judge, I want individual debaters to be ranked by their scores, so that outstanding performers can be recognized.

#### Acceptance Criteria

1. WHEN calculating individual rankings, THE System SHALL average all judge scores for each debater with two decimal precision
2. WHEN debaters have identical final scores, THE System SHALL use Logical Reasoning average as first tiebreaker
3. WHEN Logical Reasoning scores are identical, THE System SHALL use Debate Skills average as second tiebreaker
4. WHEN all tiebreaker scores are identical, THE System SHALL allow tied rankings
5. THE System SHALL display individual rankings alongside team results

### Requirement 6: Admin Flow Control

**User Story:** As an administrator, I want to control the debate flow through distinct phases, so that I can manage the competition systematically.

#### Acceptance Criteria

1. WHEN managing debate flow, THE System SHALL provide mutually exclusive controls: Enable Pre-Debate Voting, Enable Post-Debate Voting, Enable Judge Scoring, Close All Channels
2. WHEN a phase is active, THE System SHALL broadcast state changes via WebSocket to all connected clients
3. WHEN monitoring progress, THE System SHALL display real-time vote counts and submission status to admin only
4. WHEN all channels are closed, THE System SHALL enable the Reveal Results button
5. THE System SHALL prevent result revelation until all voting and scoring channels are closed

### Requirement 7: Contest Configuration

**User Story:** As an administrator, I want to configure debate details and participants, so that I can set up competitions efficiently.

#### Acceptance Criteria

1. WHEN setting up a debate, THE System SHALL allow configuration of debate topic, Pro team name, and Con team name
2. WHEN managing participants, THE System SHALL support importing debater lists with position assignments (First Speaker through Fourth Speaker)
3. WHEN managing audience, THE System SHALL support Excel batch import of audience accounts with unique credentials
4. WHEN generating judge access, THE System SHALL create unique login links for each judge
5. THE System SHALL validate all participant data before saving configuration

### Requirement 8: Display Screen Management

**User Story:** As a display screen operator, I want to show appropriate information during different phases, so that I can maintain suspense and engagement.

#### Acceptance Criteria

1. WHEN in voting phase, THE Display_Screen SHALL show QR code, debate topic, and total vote count without revealing vote distribution
2. WHEN voting is closed, THE Display_Screen SHALL show "Voting channels closed, calculating results..." message
3. WHEN results are revealed, THE Display_Screen SHALL animate bar charts showing final vote counts and individual rankings
4. WHEN displaying information, THE Display_Screen SHALL never show real-time vote distributions during voting phases
5. THE Display_Screen SHALL update immediately when receiving WebSocket state changes

### Requirement 9: Mobile Responsive Design

**User Story:** As a mobile user, I want optimized interfaces for judges and audience, so that I can participate effectively on mobile devices.

#### Acceptance Criteria

1. WHEN accessing on mobile, THE System SHALL set viewport meta tag to prevent zooming and ensure proper scaling
2. WHEN judges use mobile interface, THE System SHALL provide tab-based navigation with accordion cards to avoid horizontal scrolling
3. WHEN audience uses mobile interface, THE System SHALL provide large, touch-friendly voting buttons with clear visual feedback
4. WHEN forms are displayed on mobile, THE System SHALL use number input types to trigger numeric keyboards
5. THE System SHALL maintain consistent UI styling with the existing design system across all mobile interfaces

### Requirement 10: Data Persistence and Export

**User Story:** As an administrator, I want to export competition results, so that I can maintain records and generate reports.

#### Acceptance Criteria

1. WHEN exporting results, THE System SHALL generate Excel files containing all judge scores, vote counts, and calculated results
2. WHEN storing data, THE System SHALL maintain audit trails for all votes and score submissions with timestamps
3. WHEN calculating final results, THE System SHALL preserve all intermediate calculations for verification
4. THE System SHALL backup all competition data before result revelation
5. THE System SHALL support multiple export formats for different reporting needs