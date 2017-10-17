import Vue from 'vue/dist/vue.js'
import axios from 'axios'
import Vuetable from 'vuetable-2/src/components/Vuetable.vue'
Vue.use(Vuetable)

const msg = "Convert native2ascii for java apps";
const languageEndpoint = 'http://localhost:8800/lang';
const endpoint = 'http://localhost:8800/api';

// attach message
new Vue({
  data : {
    message: msg
  }
}).$mount('#message');

// Set languages
new Vue({
  el: '#newRecordForm',
  data: {
    languages: []
  },
  mounted() {
    this.get()
  },
  methods: {
    get: function() {
      axios.get(languageEndpoint).then(res => {
        console.log(res);
        this.languages = res.data.languages
      });
    }
  }
});

// show list view
new Vue({
  el : '#listView',
  data : {
    items: []
  },
  methods: {
    get: function () {
      axios.get(endpoint).then(response => {
        console.log(endpoint, response);
        [].slice.call(response.data).forEach(element => {
          this.items.push(element)
        })
      });
    }
  }
});

// add new record
new Vue({
  data: {
    language: '',
    key: '',
    value: '',
    description: ''
  },
  methods: {
    addNewRecord: function () {
      console.log("Called addNewRecord.");
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
});

