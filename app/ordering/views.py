# -*- coding: UTF-8 -*-
from datetime import datetime, time, timedelta
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from sqlalchemy import and_
from sqlalchemy.sql import func
from . import ordering
from .. import db
from ..decorators import moderator_required
from ..models import Order, Order_Status, Dish, Restaurant
from .forms import CreateOrderForm
from ..email import send_email

@ordering.route('/create-order/<int:dish_id>', methods=['GET', 'POST'])
@login_required
def create_order(dish_id):
	# order a dish
	dish = Dish.query.get_or_404(dish_id)
	route = dish.restaurant.route
	if dish.is_available(current_user.is_VIP):
		form = CreateOrderForm(current_user.balance)
		if request.method == 'POST':
			# time check
			if not dish.is_available(current_user.is_VIP):
				flash("Sorry, reservation time ends today~ This dish is not available now ┬＿┬")
				return redirect(url_for('main.menu'))
			# stock check
			if dish.sold_out:
				flash("Sold Out ┬＿┬")
				return redirect(url_for('main.menu'))
			# load check of the route
			if route.reach_limit:
				flash("Sold Out ┬＿┬")
				return redirect(url_for('main.menu'))

			if form.balance_pay.data == 1:
				# if user want to pay by balance
				if current_user.balance < dish.price:
					to_be_paid = dish.price - current_user.balance
					current_user.balance = 0
					pay_status = 0
				else:
					to_be_paid = 0
					current_user.balance -= dish.price
					pay_status = 1
				db.session.add(current_user)
			else:
				# if user want to pay by cash
				to_be_paid = dish.price
				pay_status = 2
			# decrease stock by one
			dish.set_stock(-1)
			db.session.add(dish)
			# increase today's dish of route by one 
			route.today_load += 1
			db.session.add(route)
			# today_id and status will be automatically determined when constructor runs
			order = Order(dish_id=dish_id, user_id=current_user.id, 
										spot_id=form.spot.data.id, 
										to_be_paid=to_be_paid, 
										price_sold=dish.price, 
										original_price=dish.original_price)
			db.session.add(order)
			db.session.commit()
			order.set_today_id(dish.name)
			db.session.add(order)
			# send confirmation email
			send_email(current_user.email, 'Order Confirmation', 'ordering/email/confirmation', order=order, user=current_user, dish=dish)
			if pay_status == 0:
				flash("Order successful! Partially paid by account balance. Please pay the remaining when you get the takeout.")
			elif pay_status == 1:
				flash("Order successful! Paid by account balance.")
			else:
				flash("Order successful! Please pay cash when you get the takeout.")
			return redirect(url_for('.invoice', order_id=order.id))
		time_now = datetime.now()
		return render_template('ordering/create_order.html', form=form, dish=dish, time_now=time_now)
	else:
		# if dish is not avaiable today, redirect to root page
		flash("Sorry~This dish is not available today ┬＿┬")
		return redirect(url_for('main.menu'))

@ordering.route('/order-history')
@login_required
def orders():
	# show all orders of current user
	orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
	return render_template('ordering/order_history.html', orders=orders)

@ordering.route('/order/<int:order_id>')
@login_required
def invoice(order_id):
	# get invoice of an order
	order = Order.query.get(order_id)
	if order is None:
		# not return 404 so that people will not know how many orders we actually have
		abort(403)
	else:
		if order.user_id == current_user.id:
			# user can see the invoice only when it belongs to him
			return render_template('ordering/invoice.html', order=order)
		else:
			abort(403)

@ordering.route('/cancel-order/<int:order_id>')
@login_required
def cancel_order(order_id):
	# cancel an order
	order = Order.query.get(order_id)
	if order is None:
		# not return 404 so that people will not know how many orders we actually have
		abort(403)
	else:
		if order.user_id == current_user.id and order.status != Order_Status.Cancelled:
			# user can only cancel his own order
			order.status = Order_Status.Cancelled
			if order.to_be_paid < order.price_sold:
				# if paid by balance, return the amount paid
				current_user.balance += order.price_sold - order.to_be_paid
				db.session.add(current_user)
			db.session.add(order)
			flash("Successful cancel the order")
			return redirect(url_for('.orders'))
		else:
			abort(403)

@ordering.route('/daily-orders-statistics')
@login_required
@moderator_required
def daily_orders_statistics():
	today = datetime.now().date()
	hour_now = datetime.now().hour
	hour_boundary = time(21)
	if hour_now < 21:
		datetime_start = datetime.combine(today, hour_boundary) + timedelta(-1)
		datetime_end = datetime.combine(today, hour_boundary)
	else:
		datetime_start = datetime.combine(today, hour_boundary) 
		datetime_end = datetime.combine(today, hour_boundary) + timedelta(1)
	# may need some improvement for the way to make query
	statistics=db.session.query(Restaurant.name.label("restaurant_name"), Dish.name.label("dish_name"), db.func.count(Dish.id).label("amount")).join(Order, Order.dish_id == Dish.id).join(Restaurant, Restaurant.id == Dish.restaurant_id).filter(and_(Order.created_at >= datetime_start, Order.created_at < datetime_end)).order_by(Restaurant.name.desc()).group_by(Dish.name, Restaurant.name).all()
	sum = db.session.query(func.count()).filter(and_(Order.created_at >= datetime_start, Order.created_at < datetime_end)).scalar()
	return render_template('ordering/daily_orders_statics.html', statistics=statistics, n =len(statistics), sum=sum)

@ordering.route('/daily-orders-printing')
@login_required
@moderator_required
def daily_orders_printing():
	orders = Order.today().order_by(Order.id).all()
	return render_template('ordering/daily_orders_printing.html', orders=orders)
