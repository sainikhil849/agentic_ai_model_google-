# BookMyShow Venue - Usage Guide for Dashboard/Frontend

## Quick Start

### Accessing Venue Information in Events

When you receive an event object from the API/database, it will have these venue-related fields:

```python
event = {
    # Original structured venue data
    "venue": {...},  # Full venue object with all details
    
    # Formatted display fields (ready to use)
    "venue_name": "Shilpakala Vedika: Hyderabad",
    "venue_full": "Shilpakala Vedika: Hyderabad\nShilparamam, Hitech, Hitech City Rd, Jubilee Enclave, Hyderabad, Telangana, 500081, India",
    "venue_city": "Hyderabad",
    "venue_summary": "Shilpakala Vedika: Hyderabad, Hyderabad"
}
```

---

## Display Formats

### 1. Venue Name (Quick Reference)
**Use for:** Small cards, lists, headers
```python
venue_name = event["venue_name"]
# Output: "Shilpakala Vedika: Hyderabad"
```

### 2. Venue Summary (Name + City)
**Use for:** List items, search results, breadcrumbs
```python
venue_summary = event["venue_summary"]
# Output: "Shilpakala Vedika: Hyderabad, Hyderabad"
```

### 3. Venue City (Filtering)
**Use for:** Location filters, grouping, city-based searches
```python
city = event["venue_city"]
# Output: "Hyderabad"
```

### 4. Venue Full Address (Detailed View)
**Use for:** Event details page, maps, directions
```python
full_address = event["venue_full"]
# Output: Multi-line formatted address
# Shilpakala Vedika: Hyderabad
# Shilparamam, Hitech, Hitech City Rd, Jubilee Enclave, Hyderabad, Telangana, 500081, India
```

---

## HTML/Template Examples

### Event Card Display
```html
<div class="event-card">
  <h3>{{ event.event_name }}</h3>
  <p class="venue">
    📍 {{ event.venue_summary }}
  </p>
  <p class="date">{{ event.event_date }}</p>
  <p class="price">₹{{ event.price }}</p>
</div>
```

### Event Details Page
```html
<div class="event-details">
  <h1>{{ event.event_name }}</h1>
  
  <div class="venue-section">
    <h3>Venue</h3>
    <div class="venue-name">
      📍 {{ event.venue_name }}
    </div>
    <div class="venue-address">
      {{ event.venue_full | linebreaks }}
    </div>
  </div>
  
  <div class="description-section">
    <h3>Description</h3>
    <p>{{ event.description }}</p>
  </div>
</div>
```

### Event List with Filtering
```html
<div class="event-list">
  {% for event in events %}
    <div class="event-item" data-city="{{ event.venue_city }}">
      <div class="event-header">
        <h4>{{ event.event_name }}</h4>
        <span class="city-badge">{{ event.venue_city }}</span>
      </div>
      <div class="event-venue">
        {{ event.venue_name }}<br>
        <small>{{ event.venue_city }}</small>
      </div>
      <div class="event-footer">
        <span class="date">{{ event.event_date }}</span>
        <span class="price">₹{{ event.price }}</span>
      </div>
    </div>
  {% endfor %}
</div>
```

---

## API Response Examples

### GET /api/events

```json
{
  "events": [
    {
      "event_name": "Live Concert",
      "event_date": "2026-04-20",
      "price": 500,
      "platform": "BookMyShow",
      "city": "Hyderabad",
      "venue_name": "Shilpakala Vedika: Hyderabad",
      "venue_summary": "Shilpakala Vedika: Hyderabad, Hyderabad",
      "venue_city": "Hyderabad",
      "venue_full": "Shilpakala Vedika: Hyderabad\nShilparamam, Hitech, Hitech City Rd, Jubilee Enclave, Hyderabad, Telangana, 500081, India",
      "description": "An exciting live concert event",
      "event_url": "https://in.bookmyshow.com/events/...",
      "organizer": "BookMyShow"
    }
  ]
}
```

### GET /api/events/{id}

```json
{
  "event": {
    "event_name": "Live Concert",
    "event_date": "2026-04-20",
    "price": 500,
    "platform": "BookMyShow",
    "venue": {
      "name": "Shilpakala Vedika: Hyderabad",
      "street_address": "Shilparamam, Hitech, Hitech City Rd, Jubilee Enclave, Hyderabad, Telangana 500081, India",
      "locality": "Hyderabad",
      "city": "Hyderabad",
      "state": "Telangana",
      "postal_code": "500081",
      "country": "India",
      "full_display": "Shilpakala Vedika: Hyderabad, Shilparamam, Hitech, Hitech City Rd, Jubilee Enclave, Hyderabad, Telangana, 500081, India"
    },
    "venue_name": "Shilpakala Vedika: Hyderabad",
    "venue_summary": "Shilpakala Vedika: Hyderabad, Hyderabad",
    "venue_city": "Hyderabad",
    "venue_full": "Shilpakala Vedika: Hyderabad\nShilparamam, Hitech, Hitech City Rd, Jubilee Enclave, Hyderabad, Telangana, 500081, India",
    "description": "An exciting live concert event",
    "event_url": "https://in.bookmyshow.com/events/..."
  }
}
```

---

## React Component Example

```jsx
import React from 'react';

const EventCard = ({ event }) => {
  return (
    <div className="event-card">
      <div className="event-header">
        <h3>{event.event_name}</h3>
        <span className="platform-badge">{event.platform}</span>
      </div>
      
      <div className="event-details">
        <div className="detail-item">
          <span className="label">📅 Date:</span>
          <span className="value">{event.event_date}</span>
        </div>
        
        <div className="detail-item">
          <span className="label">💰 Price:</span>
          <span className="value">₹{event.price}</span>
        </div>
        
        <div className="detail-item">
          <span className="label">📍 Venue:</span>
          <span className="value">{event.venue_summary}</span>
        </div>
        
        <div className="detail-item full-width">
          <span className="label">📌 Address:</span>
          <div className="value address">
            {event.venue_full.split('\n').map((line, i) => (
              <div key={i}>{line}</div>
            ))}
          </div>
        </div>
        
        <div className="detail-item full-width">
          <span className="label">📝 Description:</span>
          <p className="value">{event.description}</p>
        </div>
      </div>
      
      <div className="event-actions">
        <a href={event.event_url} target="_blank" rel="noopener noreferrer">
          View on {event.platform}
        </a>
      </div>
    </div>
  );
};

export default EventCard;
```

### Event Details Page Component

```jsx
const EventDetailsPage = ({ eventId }) => {
  const [event, setEvent] = React.useState(null);
  
  React.useEffect(() => {
    fetch(`/api/events/${eventId}`)
      .then(res => res.json())
      .then(data => setEvent(data.event));
  }, [eventId]);
  
  if (!event) return <div>Loading...</div>;
  
  return (
    <div className="event-details-page">
      <h1>{event.event_name}</h1>
      
      <div className="info-section">
        <h2>Venue Information</h2>
        <div className="venue-info">
          <h3>{event.venue_name}</h3>
          <p className="address">
            {event.venue_full.split('\n').map((line, i) => (
              <span key={i}>
                {line}
                {i < event.venue_full.split('\n').length - 1 && <br />}
              </span>
            ))}
          </p>
        </div>
      </div>
      
      <div className="info-section">
        <h2>About this Event</h2>
        <p>{event.description}</p>
      </div>
      
      <div className="info-section">
        <h2>Event Details</h2>
        <table>
          <tbody>
            <tr>
              <td>Date</td>
              <td>{event.event_date}</td>
            </tr>
            <tr>
              <td>Price</td>
              <td>₹{event.price}</td>
            </tr>
            <tr>
              <td>Platform</td>
              <td>{event.platform}</td>
            </tr>
            <tr>
              <td>Organizer</td>
              <td>{event.organizer}</td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div className="actions">
        <a href={event.event_url} className="btn-primary">
          Book Tickets on {event.platform}
        </a>
      </div>
    </div>
  );
};
```

---

## Vue.js Example

```vue
<template>
  <div class="event-card">
    <div class="event-header">
      <h3>{{ event.event_name }}</h3>
      <span class="platform">{{ event.platform }}</span>
    </div>
    
    <div class="event-info">
      <div class="info-row">
        <span class="icon">📅</span>
        <span>{{ event.event_date }}</span>
      </div>
      
      <div class="info-row">
        <span class="icon">💰</span>
        <span>₹{{ event.price }}</span>
      </div>
      
      <div class="info-row">
        <span class="icon">📍</span>
        <span>{{ event.venue_summary }}</span>
      </div>
    </div>
    
    <div class="venue-details">
      <h4>Full Address</h4>
      <p v-for="(line, idx) in venueFull" :key="idx">
        {{ line }}
      </p>
    </div>
    
    <div class="description">
      <h4>Description</h4>
      <p>{{ event.description }}</p>
    </div>
    
    <a :href="event.event_url" target="_blank" class="btn">
      Book Now
    </a>
  </div>
</template>

<script>
export default {
  props: {
    event: Object
  },
  computed: {
    venueFull() {
      return this.event.venue_full.split('\n');
    }
  }
};
</script>

<style scoped>
.event-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.venue-details {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 6px;
  margin: 15px 0;
}

.venue-details p {
  margin: 5px 0;
  font-size: 14px;
}
</style>
```

---

## Filtering Events by City

```javascript
// Get all events for Hyderabad
const hyderabadEvents = events.filter(e => e.venue_city === 'Hyderabad');

// Get unique cities
const cities = [...new Set(events.map(e => e.venue_city))];

// Group by city
const eventsByCity = events.reduce((acc, event) => {
  const city = event.venue_city;
  if (!acc[city]) acc[city] = [];
  acc[city].push(event);
  return acc;
}, {});

// Usage
Object.keys(eventsByCity).forEach(city => {
  console.log(`${city}: ${eventsByCity[city].length} events`);
});
```

---

## Styling Tips

### CSS Classes for Venue Display

```css
.venue-name {
  font-weight: bold;
  font-size: 16px;
  color: #333;
}

.venue-address {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  white-space: pre-wrap;  /* Preserve line breaks */
  margin: 10px 0;
}

.venue-city {
  font-size: 12px;
  background: #f0f0f0;
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
}

.venue-summary {
  font-size: 13px;
  color: #555;
}
```

---

## Common Operations

### 1. Display Venue in Event List

```python
# Backend returns:
{
  "events": [
    {"venue_name": "...", "venue_city": "...", ...},
    ...
  ]
}

# Frontend displays:
for event in events:
    print(f"{event.venue_name}, {event.venue_city}")
```

### 2. Show Full Address on Click

```javascript
function showFullAddress(event) {
  alert(event.venue_full);
  // Or display in modal/popup
}
```

### 3. Map Integration

```javascript
// Extract coordinates for map
function getMapUrl(event) {
  const address = encodeURIComponent(event.venue_full);
  return `https://maps.google.com/maps?q=${address}`;
}

// Usage:
<a href={getMapUrl(event)} target="_blank">
  View on Maps
</a>
```

### 4. Event Grouping by Venue

```python
from collections import defaultdict

venues = defaultdict(list)
for event in events:
    venues[event.venue_name].append(event)

for venue, events_at_venue in venues.items():
    print(f"{venue}: {len(events_at_venue)} events")
```

---

## Export to Different Formats

### To CSV
```python
import csv

def export_to_csv(events, filename):
    with open(filename, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'event_name', 'event_date', 'price',
            'venue_name', 'venue_full', 'venue_city',
            'description', 'event_url'
        ])
        writer.writeheader()
        writer.writerows([{
            'event_name': e['event_name'],
            'event_date': e['event_date'],
            'price': e['price'],
            'venue_name': e['venue_name'],
            'venue_full': e['venue_full'].replace('\n', ' | '),
            'venue_city': e['venue_city'],
            'description': e['description'],
            'event_url': e['event_url']
        } for e in events])
```

### To JSON
```python
import json

def export_to_json(events, filename):
    with open(filename, 'w') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
```

---

## Performance Notes

- `venue_name` - Use for quick display (10-50 chars)
- `venue_city` - Use for filtering/searching (very fast)
- `venue_summary` - Use for short display (20-100 chars)
- `venue_full` - Use for detailed view (100-500 chars)

All fields are pre-computed - no additional processing needed!

---

## Support

For issues or questions about venue data:
1. Check `BOOKMYSHOW_VENUE_IMPLEMENTATION.md` for technical details
2. Run `test_venue_validator.py` to verify data correctness
3. Review test cases for expected behavior
4. Check event object structure in API responses

---

**Version**: 1.0  
**Last Updated**: April 19, 2026  
**Status**: Ready for Production ✓
