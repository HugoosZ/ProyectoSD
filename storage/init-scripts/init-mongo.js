db.getSiblingDB('waze_events').createUser({
    user: "waze_user",
    pwd: "securepassword",
    roles: [{
      role: "readWrite",
      db: "waze_events"
    }]
  });