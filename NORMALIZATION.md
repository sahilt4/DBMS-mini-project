# Database Normalization Analysis
## Bus Reservation and Management System (BRMS) | DBMS Mini Project

---

## 1. Introduction to Normalization in BRMS

Database Normalization is the systematic mathematical technique of organizing data in a relational database to minimize data redundancy and eliminate undesirable update, insertion, and deletion anomalies.

In this project, the **Bus Reservation and Management System (BRMS)** schema was progressively decomposed from an unnormalized universal relation into **First Normal Form (1NF)**, **Second Normal Form (2NF)**, **Third Normal Form (3NF)**, and verified for **Boyce-Codd Normal Form (BCNF)**.

---

## 2. Universal Unnormalized Relation (UNF)

Consider a naive, unnormalized single-table design representing the bus reservation domain:

$$\text{UNIVERSAL\_BOOKING}(\underline{\text{booking\_ref}}, \text{booking\_date}, \text{passenger\_name}, \text{passenger\_phone}, \text{passenger\_age}, \text{passenger\_gender}, \text{bus\_reg\_no}, \text{bus\_name}, \text{bus\_type}, \text{bus\_capacity}, \text{route\_source}, \text{route\_dest}, \text{route\_distance}, \text{departure\_time}, \text{arrival\_time}, \text{fare}, \text{seat\_numbers}, \text{stops\_list}, \text{payment\_method}, \text{txn\_ref}, \text{payment\_status})$$

### Anomalies in UNF:
1. **Multivalued Attributes & Repeating Groups**:
   - `seat_numbers`: A single booking could reserve multiple seats (e.g. `"12, 13, 14"`).
   - `stops_list`: A route contains an ordered list of intermediate cities and arrival offsets (e.g. `"Lonavala (45m), Khandala (60m)"`).
2. **Massive Redundancy**:
   - For every ticket sold on a bus trip, the bus details (`bus_name`, `bus_type`, `capacity`) and route details (`route_source`, `route_dest`, `route_distance`) are repeated identically across hundreds of rows.
3. **Severe Anomalies**:
   - **Insertion Anomaly**: We cannot record a newly purchased bus in the fleet or create a new route until at least one passenger books a seat on that trip.
   - **Deletion Anomaly**: If the only passenger who booked a trip cancels their ticket, deleting that row completely erases the bus information, route geography, and timetable from the database.
   - **Update Anomaly**: If a bus's capacity changes or a route's distance is corrected, every single past and future ticket record must be found and updated; missing even one leads to inconsistent state.

---

## 3. First Normal Form (1NF)

### Definition of 1NF:
A relation $R$ is in 1NF if and only if:
1. Every attribute domain contains only **atomic** (indivisible) values.
2. There are **no repeating groups** or multivalued arrays.
3. Each record is uniquely identifiable by a primary key.

### Decomposition into 1NF:
1. Decomposed multivalued comma-separated `seat_numbers` into individual rows so each booking row corresponds to **exactly one seat**.
2. Extracted the repeating `stops_list` into a dedicated relation where each row represents one distinct stop waypoint.
3. Added surrogate keys (`user_id`, `passenger_id`, `bus_id`, `route_id`, `schedule_id`, `booking_id`) to ensure distinct identity.

---

## 4. Second Normal Form (2NF)

### Definition of 2NF:
A relation $R$ is in 2NF if and only if:
1. It is in **1NF**.
2. **No non-prime attribute is partially dependent on any candidate key**. (Every non-key attribute must be fully functionally dependent on the entire primary key, not a proper subset of it).

### Identification of Partial Dependencies:
Consider a composite relation such as:
$$\text{SCHEDULE\_SEAT\_ASSIGNMENT}(\underline{\text{schedule\_id}, \text{seat\_number}}, \text{bus\_name}, \text{bus\_capacity}, \text{seat\_status})$$
- Candidate Key: `(schedule_id, seat_number)`
- Functional Dependencies:
  - $\text{schedule\_id}, \text{seat\_number} \to \text{seat\_status}$ (Full dependency)
  - $\text{schedule\_id} \to \text{bus\_name}, \text{bus\_capacity}$ (**Partial dependency!** Depends only on `schedule_id`, not on `seat_number`).

Consider intermediate stops along a route:
$$\text{ROUTE\_WAYPOINT}(\underline{\text{route\_id}, \text{stop\_sequence}}, \text{stop\_id}, \text{stop\_name}, \text{stop\_city}, \text{distance\_from\_origin})$$
- Candidate Key: `(route_id, stop_sequence)`
- $\text{stop\_id} \to \text{stop\_name}, \text{stop\_city}$ (**Partial dependency!** Stop details depend only on the stop, not on the route sequence).

### Decomposition to Achieve 2NF:
1. Split out `BUSES` from `SCHEDULES`:
   - `BUSES` ($\underline{\text{bus\_id}}$, registration_number, bus_name, bus_type, capacity, operational_status)
   - `SCHEDULES` ($\underline{\text{schedule\_id}}$, bus_id, route_id, departure_datetime, arrival_datetime, base_fare)
   - `SCHEDULE_SEATS` ($\underline{\text{schedule\_seat\_id}}$, schedule_id, seat_number, seat_status)
2. Split out `BUS_STOPS` from `ROUTE_STOPS`:
   - `BUS_STOPS` ($\underline{\text{stop\_id}}$, stop_name, city, address)
   - `ROUTE_STOPS` ($\underline{\text{route\_stop\_id}}$, route_id, stop_id, stop_sequence, distance_from_origin, arrival_offset_minutes)

Now every non-prime attribute depends strictly on the entire candidate key.

---

## 5. Third Normal Form (3NF)

### Definition of 3NF:
A relation $R$ is in 3NF if and only if:
1. It is in **2NF**.
2. **No transitive functional dependencies exist** for non-prime attributes.
   - For every functional dependency $X \to Y$, either:
     - $X$ is a superkey of $R$, OR
     - $Y$ is a prime attribute (part of a candidate key).

### Identification of Transitive Dependencies:
Consider the reservation and payment relation before 3NF decomposition:
$$\text{BOOKING\_PAYMENT}(\underline{\text{booking\_id}}, \text{booking\_ref}, \text{passenger\_id}, \text{schedule\_id}, \text{total\_amount}, \text{payment\_method}, \text{txn\_ref}, \text{payment\_status}, \text{refund\_amount}, \text{refund\_date})$$

- Functional Dependencies:
  - $\text{booking\_id} \to \text{txn\_ref}$
  - $\text{txn\_ref} \to \text{payment\_method}, \text{payment\_status}$
  - $\text{booking\_id} \to \text{payment\_status}$ is **transitive** through $\text{txn\_ref}$!
  - Furthermore, if a ticket is refunded:
    $\text{booking\_id} \to \text{refund\_id} \to \text{refund\_amount}, \text{refund\_reason}$ (transitive dependency).

Consider passenger accounts:
$$\text{PASSENGER\_USER}(\underline{\text{passenger\_id}}, \text{user\_id}, \text{email}, \text{password\_hash}, \text{role}, \text{full\_name}, \text{age}, \text{gender})$$
- $\text{passenger\_id} \to \text{user\_id}$
- $\text{user\_id} \to \text{email}, \text{password\_hash}, \text{role}$
- $\text{passenger\_id} \to \text{role}$ is **transitive**!

### Decomposition to Achieve 3NF:
Decompose relations to isolate transitive dependencies:
1. Separate `USERS` and `PASSENGERS`:
   - `USERS` ($\underline{\text{user\_id}}$, email, password_hash, role, phone, account_status)
   - `PASSENGERS` ($\underline{\text{passenger\_id}}$, user_id, full_name, age, gender, phone)
2. Separate `BOOKINGS`, `PAYMENTS`, and `REFUNDS`:
   - `BOOKINGS` ($\underline{\text{booking\_id}}$, booking_reference, passenger_id, schedule_id, seat_number, total_amount, booking_status)
   - `PAYMENTS` ($\underline{\text{payment\_id}}$, booking_id, amount, payment_method, transaction_reference, payment_status)
   - `REFUNDS` ($\underline{\text{refund\_id}}$, payment_id, booking_id, refund_amount, refund_reason, refund_status)
3. Separate `TICKET_CHECKINS`:
   - `TICKET_CHECKINS` ($\underline{\text{checkin\_id}}$, booking_id, checkin_datetime, verified_by_user_id, checkin_method, boarding_stop_id)

All non-prime attributes in every table now depend directly and only on the primary key ($X \to Y \implies X \text{ is superkey}$).

---

## 6. Boyce-Codd Normal Form (BCNF)

### Definition of BCNF:
A relation $R$ is in BCNF if and only if for **every non-trivial functional dependency** $X \to Y$, $X$ is a **superkey**. (BCNF is a stricter version of 3NF that eliminates anomalies when a relation has multiple overlapping composite candidate keys).

### BCNF Verification of BRMS Entities:

#### Relation: `USERS`
- Candidate Keys: `user_id`, `email`.
- FDs:
  - $\text{user\_id} \to \text{email}, \text{full\_name}, \text{password\_hash}, \text{role}, \text{phone}, \text{account\_status}$ (LHS is superkey).
  - $\text{email} \to \text{user\_id}, \text{full\_name}, \text{password\_hash}, \text{role}, \text{phone}, \text{account\_status}$ (LHS is superkey).
- **Result**: In BCNF.

#### Relation: `BUSES`
- Candidate Keys: `bus_id`, `registration_number`.
- FDs:
  - $\text{bus\_id} \to \text{registration\_number}, \text{bus\_name}, \text{bus\_type}, \text{capacity}, \text{operational\_status}$ (LHS is superkey).
  - $\text{registration\_number} \to \text{bus\_id}, \dots$ (LHS is superkey).
- **Result**: In BCNF.

#### Relation: `ROUTE_STOPS`
- Candidate Keys: `route_stop_id`, `(route_id, stop_sequence)`, `(route_id, stop_id)`.
- FDs:
  - $\text{route\_stop\_id} \to \text{route\_id}, \text{stop\_id}, \text{stop\_sequence}, \text{distance\_from\_origin}, \text{arrival\_offset\_minutes}$ (LHS is superkey).
  - $(\text{route\_id}, \text{stop\_sequence}) \to \text{route\_stop\_id}, \text{stop\_id}, \dots$ (LHS is superkey).
  - $(\text{route\_id}, \text{stop\_id}) \to \text{route\_stop\_id}, \text{stop\_sequence}, \dots$ (LHS is superkey).
- **Result**: In BCNF.

#### Relation: `SCHEDULE_SEATS`
- Candidate Keys: `schedule_seat_id`, `(schedule_id, seat_number)`.
- FDs:
  - $\text{schedule\_seat\_id} \to \text{schedule\_id}, \text{seat\_number}, \text{seat\_status}$ (LHS is superkey).
  - $(\text{schedule\_id}, \text{seat\_number}) \to \text{schedule\_seat\_id}, \text{seat\_status}$ (LHS is superkey).
- **Result**: In BCNF.

#### Relation: `BOOKINGS`
- Candidate Keys: `booking_id`, `booking_reference`.
- FDs:
  - $\text{booking\_id} \to \text{booking\_reference}, \text{passenger\_id}, \text{schedule\_id}, \text{seat\_number}, \text{total\_amount}, \text{booking\_status}$ (LHS is superkey).
  - $\text{booking\_reference} \to \text{booking\_id}, \dots$ (LHS is superkey).
- **Result**: In BCNF.

---

## 7. Functional Dependencies Summary Table

| Relation | Determinant ($X$) | Dependent Attributes ($Y$) | Is $X$ a Superkey? | Normal Form Achieved |
|---|---|---|---|---|
| `users` | `user_id` | `email`, `full_name`, `password_hash`, `role`, `status` | Yes | BCNF |
| `users` | `email` | `user_id`, `full_name`, `password_hash`, `role`, `status` | Yes | BCNF |
| `passengers` | `passenger_id` | `user_id`, `full_name`, `age`, `gender`, `phone` | Yes | BCNF |
| `buses` | `bus_id` | `registration_number`, `bus_name`, `bus_type`, `capacity` | Yes | BCNF |
| `buses` | `registration_number` | `bus_id`, `bus_name`, `bus_type`, `capacity` | Yes | BCNF |
| `routes` | `route_id` | `source`, `destination`, `distance`, `estimated_duration` | Yes | BCNF |
| `bus_stops` | `stop_id` | `stop_name`, `city`, `address` | Yes | BCNF |
| `route_stops` | `route_stop_id` | `route_id`, `stop_id`, `stop_sequence`, `distance` | Yes | BCNF |
| `route_stops` | `(route_id, stop_seq)` | `route_stop_id`, `stop_id`, `distance`, `offset` | Yes | BCNF |
| `schedules` | `schedule_id` | `bus_id`, `route_id`, `departure`, `arrival`, `fare` | Yes | BCNF |
| `schedule_seats`| `schedule_seat_id` | `schedule_id`, `seat_number`, `seat_status` | Yes | BCNF |
| `schedule_seats`| `(sched_id, seat_no)` | `schedule_seat_id`, `seat_status` | Yes | BCNF |
| `bookings` | `booking_id` | `booking_reference`, `passenger_id`, `schedule_id`, `seat` | Yes | BCNF |
| `bookings` | `booking_reference` | `booking_id`, `passenger_id`, `schedule_id`, `seat` | Yes | BCNF |
| `payments` | `payment_id` | `booking_id`, `amount`, `payment_method`, `txn_ref` | Yes | BCNF |
| `payments` | `txn_ref` | `payment_id`, `booking_id`, `amount`, `payment_method` | Yes | BCNF |
| `refunds` | `refund_id` | `payment_id`, `booking_id`, `refund_amount`, `reason` | Yes | BCNF |
| `waitlist` | `waitlist_id` | `passenger_id`, `schedule_id`, `queue_position` | Yes | BCNF |
| `ticket_checkins`| `checkin_id` | `booking_id`, `checkin_datetime`, `verified_by_user_id`| Yes | BCNF |
| `ticket_checkins`| `booking_id` | `checkin_id`, `checkin_datetime`, `verified_by_user_id`| Yes | BCNF |

---

## 8. Anomaly Resolution Matrix

| Anomaly Type | Unnormalized Relation (UNF) Problem | Normalized BRMS Solution |
|---|---|---|
| **Insertion Anomaly** | Cannot create a new bus route or add a bus to the fleet without an existing booking. | `BUSES` and `ROUTES` exist as independent entities; buses and routes can be registered without any schedules or bookings. |
| **Deletion Anomaly** | Deleting the last passenger's booking from a trip deletes the bus, route, and stop information. | Deleting or cancelling a booking only updates `bookings` and `schedule_seats`; `schedules`, `buses`, and `routes` remain untouched. |
| **Update Anomaly** | Changing the bus fare or route distance requires updating every historical booking row. | Fare is defined at the `schedules` level; route distance is defined in `routes`. Updating either modifies exactly one row. |
| **Double-Booking Anomaly**| Multiple simultaneous bookings could claim the same seat on a schedule. | `schedule_seats` row-level locking + partial unique index `idx_bookings_active_seat` mathematically prevents duplicate active bookings. |

