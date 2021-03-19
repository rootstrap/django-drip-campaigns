Extending Django Drip
=====================

Django Drip provides a way for you to extend all the functionality through abstract classes.

These classes provide all the functions required to make a drip work, but they don't provide any data column.
Beware though, these classes use the attributes from the concrete drip classes shown in the rest of the docs.

For you to extend them you need to overwite the implementations on your own.
Since this classes handle themselves mainly through related models, as long as you maintain the inteface you can extend in any way you want.

`AbstractDrip`

This provides the data model for the drip, here you can customize the data model of the message itself.
It has a `drip` property with the actual logic of sending the message.


`AbstractSentDrip`

This provides the data model for the log of sent drips.
This will help you if you want to customize what's being saved on the database after a message is sent.
Defines a relationship with the User model of your app, that you can access through `user.sent_drips`.
Defines a relationship with the Drip model. You can access that relationship through `drip.sent_drips`.


`AbstractQuerySetRule`

This provides the query rules applied for sending the drips.
Defines a relationship with the Drip model. You can access that relationship through `drip.queryset_rules`.
