import configPublic from './config-public';
import * as env from '$env/static/private';

export default {
	...configPublic
	// SOME_KEY: env.SOME_KEY
};
