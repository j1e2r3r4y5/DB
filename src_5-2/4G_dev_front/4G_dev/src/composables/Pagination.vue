<template>
    <div class="pagination-wrapper" style="display: flex; justify-content: flex-start; align-items: center;">
        <el-pagination background layout=" total,sizes, prev, pager, next, jumper" :total="total" :page-size="pageSize"
            :current-page="currentPage" :page-sizes="pageSizes" @size-change="onSizeChange"
            @current-change="onCurrentChange" :prev-text="'上一页'" :next-text="'下一页'" :hide-on-single-page="false" />
    </div>
</template>

<script setup>
const props = defineProps({
    total: { type: Number, required: true },
    pageSize: { type: Number, default: 10 },
    currentPage: { type: Number, default: 1 },
    pageSizes: { type: Array, default: () => [5, 10, 20, 50, 100] }
})
const emit = defineEmits(['size-change', 'current-change'])
function onSizeChange(size) {
    emit('size-change', size)
}
function onCurrentChange(page) {
    emit('current-change', page)
}
</script>

<style scoped>
.pagination-wrapper {
    margin: 16px 0 0 0;
}
</style>