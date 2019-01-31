define(["source"], function (s) {
	return function (args, argsb) {
		console.log("this has args too!");
		args[0] = 42;
	};
});
