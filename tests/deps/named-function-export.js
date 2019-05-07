define(["some/module"], function (module) {
	var func = function (args) {
		console.dir(this);
		this.a = args[0];
		this.b = args[1];

		return this;
	};
	return func;
});
