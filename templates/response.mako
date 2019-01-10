<%inherit file="base.mako"/>

<div id="body" class="container">
	<div class="row">
		<div class="col-md-9">

<h1>Comparing answers for <a href="/survey/${survey.id}">${survey.name}</a>
% if theirs.privacy == "public" or theirs.privacy == "friends":
with ${theirs.user.username}
% else:
with [hidden]
% endif
</h1>
<p>${survey.long_description or ""}</p>

<%
things = []
for my_answer in response.answers:
	for their_answer in theirs.answers:
		if my_answer.question.matches(their_answer.question):
			score = my_answer.value + their_answer.value
			if score > 2:
				if my_answer.question == their_answer.question:
					if my_answer.value == their_answer.value:
						thing = 'You both %s "%s"' % (
							my_answer.value_name(), my_answer.question.text
						)
					else:
						thing = 'You %s / they %s "%s"' % (
							my_answer.value_name(),
							their_answer.value_name(), my_answer.question.text
						)
				else:
					thing = 'You %s "%s" and they %s "%s"' % (
						my_answer.value_name(), my_answer.question.text,
						their_answer.value_name(), their_answer.question.text
					)
				things.append((-score, -their_answer.value, my_answer.question.order, thing))
%>
<ul>
	% for score, their_score, order, thing in sorted(things):
		% if -score == 4:
			<li><b>${thing}</b></li>
		% else:
			<li>${thing}</li>
		% endif
	% endfor
</ul>

		</div>
		<div class="col-md-3">
			% if friends and others:
				<p>Friends who did this:
				<ul>
				% for fresponse in friends:
					<li><a href="/response/${fresponse.id}">${fresponse.user.username}</a></li>
				% endfor
				</ul>

				<p>Other people who did this:
				<ul>
				% for oresponse in others:
					<li><a href="/response/${oresponse.id}">${oresponse.user.username}</a></li>
				% endfor
				</ul>
			% endif
		</div>
	</div>
</div>
