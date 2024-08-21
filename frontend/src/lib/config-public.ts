import * as envPublic from '$env/static/public';

export default {
	PUBLIC_API_WS: envPublic.PUBLIC_API_WS || 'ws://localhost:8000/checkboxes'
};
