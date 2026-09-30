# SmartQueue — Final Hackathon Build

## Problem alignment
**The Wait Nobody Tracks: Managing Peak-Hour Queues Across Campus**

Official framing used for this build:
- 200+ students during a 45-minute break
- manual ordering and slow billing
- long queues and mixed-up orders
- cold food and unsold waste
- students skipping lunch to reach class
- the same visibility problem can extend to library/admin service points
- core question: make campus wait times **visible and manageable**, starting with the canteen

## Final product flow
### Student
Login → Choose service point → Menu → Cart → Place order → Digital token → Queue position + people ahead → Live ETA → Preparing → Ready → Assigned counter → Collected → Completed

The student does **not** need to stand in the physical queue while the order is being prepared.

### Admin
Login → Live Control → See token/order/items → Set ETA → Assign counter → Send free-form message → Start Preparing → Mark Ready → Collected → DONE

Completed orders leave the pending queue while remaining orders stay visible.

## Intelligence layer
- FIFO queue ordering
- ETA from queue position, service history and active counters
- live queue position and people-ahead count
- counter capacity awareness
- service records for actual duration
- demand/sales aggregation by menu item
- waste tracking and waste-risk flag
- peak-window decision panel
- congestion/capacity decision support
- notifications stored for order updates

## Data structures / algorithm story
The project intentionally uses practical patterns inspired by common DSA problems:
- queue/FIFO → fair order processing
- moving average → service-time estimation
- frequency aggregation → popular-item demand
- rate limiting/notification throttling → scalable alerts
- time-window aggregation → operational analytics
- task scheduling → preparation/counter capacity
- circular/bounded queue concepts → service capacity
- caching concepts → fast repeated reads

## Important prototype limitation
Authentication is intentionally demo-only. Credentials are fixed for the hackathon prototype. This is not production authentication.

## 5-minute demo
1. Student login.
2. Open GCU Main Canteen.
3. Add Veg Burger + Fries.
4. Place order.
5. Show token, queue position, ETA and order stages.
6. Open Admin login.
7. Show the same token and items in Live Control.
8. Set ETA, counter and a custom message.
9. Start Preparing.
10. Mark Ready.
11. Student screen updates live.
12. Mark Collected, then DONE.
13. Show that the completed order disappears from pending.
14. Open AI & Operations.
15. Show live orders, ETA, counters, demand and waste-risk insight.

## Key judge sentence
> SmartQueue does not merely digitize food ordering. It makes campus waiting time visible, predictable and operationally manageable.
