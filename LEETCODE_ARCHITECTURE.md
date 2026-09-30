# SmartQueue — LeetCode-derived engineering patterns

This build uses familiar DSA/design patterns from the supplied LeetCode list:

- **217 Contains Duplicate** → set/dictionary style uniqueness checks for identifiers.
- **346 Moving Average from Data Stream** → rolling service-time/throughput measurements.
- **347 Top K Frequent Elements** → useful pattern for popular menu-item analytics.
- **359 Logger Rate Limiter** → notification/message throttling pattern for future alerts.
- **362 Design Hit Counter** → time-window event aggregation for queue/order throughput.
- **621 Task Scheduler** → capacity and scheduling reasoning for service counters.
- **622 Design Circular Queue** → queue-state design and bounded queue concepts.
- **146 LRU Cache** → cache design pattern for frequently accessed menu/dashboard data.
- **1603 Design Parking System** → multi-counter capacity-management analogy.

The actual SmartQueue queue policy remains FIFO; these patterns support the surrounding analytics, capacity, uniqueness, and time-window logic rather than replacing the core queue rule.
