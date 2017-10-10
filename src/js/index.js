import Vue from 'vue/dist/vue.js'
import axios from 'axios'

const msg = "Convert native2ascii for java apps"
const endpoint = 'http://localhost:8800/api'

/**
 *
 */
export function get(url) {
  let result = [];
  axios.get(url).then(response => {
    [].slice.call(response.data).forEach(element => {
      result.push(element)
    })
  })
  return result
}

export function post(url, json) {
  axios.post(url, json).then(response => {
    console.log(response)
  })
}

const items = get(endpoint)
console.log(items)

window.addEventListener('load', () => {

  const app = new Vue({
    data : {
      message: msg
    },
    created : () => {
    }
  }).$mount('#message')

  new Vue({
    el : '#contents',
    data : {
      items : items
    }
  })

  new Vue({
    data: {
	  language: '',
	  key: '',
	  value: '',
	  description: ''
	},
	methods: {
	  addNewRecord: () => {
	    post(endpoint, {
		  // TODO: implements
	      language: 'ja',
	      key: 'key1',
	      value: 'value1',
	      description: 'description1'
	    })
	  }
	}
  })

})
