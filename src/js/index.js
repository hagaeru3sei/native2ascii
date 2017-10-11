import Vue from 'vue/dist/vue.js'
import axios from 'axios'

const msg = "Convert native2ascii for java apps"
const endpoint = 'http://localhost:8800/api'

export function get(url) {
  let result = [];
  axios.get(url).then(response => {
    [].slice.call(response.data).forEach(element => {
      result.push(element)
    })
  })
  return result
}

const items = get(endpoint)
console.log(items)

window.addEventListener('load', () => {
  // attach message
  new Vue({
    data : {
      message: msg
    },
    created : () => {
    }
  }).$mount('#message')

  // show list view
  new Vue({
    el : '#contents',
    data : {
      items : items
    }
  })
}, false)

// add new record
new Vue({
  el: '#newRecord',
  data: {
    language: '',
    key: '',
    value: '',
    description: ''
  },
  methods: {
    addNewRecord: () => {
      console.log("Called addNewRecord.")
      axios.post(endpoint, {
        language: this.language,
        key: this.key,
        value: this.value,
        description: this.description
      }).then(response =>
        console.log(response)
      )
    }
  }
})

