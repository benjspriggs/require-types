define(["dep/one"], function(one) {
	var i = one;

	define(["dep/another"], function (another) {
		var j = another[1];
	});
});
