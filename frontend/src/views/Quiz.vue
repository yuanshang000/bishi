<template>
  <div class="quiz-container">
    <!-- 加载遮罩层 -->
    <el-dialog
      v-model="creating"
      :show-close="false"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      width="450px"
      align-center
      class="loading-dialog"
    >
      <div class="loading-content">
        <el-icon class="loading-icon" :size="60" color="#409EFF">
          <Loading />
        </el-icon>
        <h3>{{ loadingText }}</h3>
        <p>{{ loadingSubText }}</p>
        <!-- 显示使用的文档信息 -->
        <div v-if="sourceDocumentsInfo && sourceDocumentsInfo.length > 0" class="source-documents-info">
          <p style="margin: 10px 0 5px 0; color: #606266; font-size: 13px; font-weight: bold;">📚 根据以下文档出题：</p>
          <div v-for="(doc, index) in sourceDocumentsInfo" :key="index" class="doc-item">
            <el-tag :type="getDocTypeTag(doc.doc_type)" size="small" style="margin-right: 5px;">
              {{ getDocTypeLabel(doc.doc_type) }}
            </el-tag>
            <span style="font-size: 13px; font-weight: 500; color: #303133;">{{ doc.title }}</span>
          </div>
        </div>
        <!-- 显示后端分割给AI的内容预览 -->
        <div v-if="sourceChunksInfo && sourceChunksInfo.length > 0" style="margin-top: 10px;">
          <p style="margin: 10px 0 5px 0; color: #606266; font-size: 13px; font-weight: bold;">🔎 文档分块预览：</p>
          <div v-for="(chunk, idx) in sourceChunksInfo.slice(0,6)" :key="idx" style="margin-bottom: 6px;">
            <el-tag :type="getDocTypeTag(chunk.doc_type)" size="small" style="margin-right: 5px;">
              {{ getDocTypeLabel(chunk.doc_type) }}
            </el-tag>
            <span style="font-size: 12px; color: #909399;">#{{ chunk.index }} · {{ chunk.title }}</span>
            <div style="font-size: 12px; color: #606266; margin-top: 3px; line-height: 1.4;">{{ chunk.preview }}</div>
          </div>
        </div>
        <div v-if="ragContextPreview" style="margin-top: 10px;">
          <p style="margin: 10px 0 5px 0; color: #606266; font-size: 13px; font-weight: bold;">🧠 输入给AI的上下文：</p>
          <div style="font-size: 12px; color: #606266; max-height: 150px; overflow: auto; background: #f5f7fa; padding: 8px; border-radius: 6px; white-space: pre-wrap;">{{ ragContextPreview }}</div>
        </div>
        <div v-if="rulesPreview" style="margin-top: 10px;">
          <p style="margin: 10px 0 5px 0; color: #606266; font-size: 13px; font-weight: bold;">📏 出题规则预览（当前选择）：</p>
          <div style="font-size: 12px; color: #606266; max-height: 150px; overflow: auto; background: #f5f7fa; padding: 8px; border-radius: 6px; white-space: pre-wrap;">{{ rulesPreview }}</div>
        </div>
        <el-progress :percentage="loadingProgress" :indeterminate="true" :duration="3" />
      </div>
    </el-dialog>

    <!-- 创建练习表单 -->
    <el-card v-if="!currentQuiz" class="practice-center-card">
      <template #header>
        <div class="quiz-header">
          <span class="quiz-title">练习中心</span>
          <!-- 练习方式切换按钮 -->
          <div class="mode-switch">
            <el-radio-group v-model="quizForm.practice_mode" size="large">
              <el-radio-button label="chapter" class="large-radio">章节练习</el-radio-button>
              <el-radio-button label="random" class="large-radio">综合训练</el-radio-button>
              <el-radio-button label="comprehensive" class="large-radio">推荐训练</el-radio-button>
            </el-radio-group>
          </div>
          <!-- 占位元素，用于保持中间对齐 -->
          <div style="width: 100px;"></div>
        </div>
      </template>

      <el-form :inline="true" class="quiz-form" size="large" style="margin-top: 30px;">
        <!-- 章节选择（章节练习 或 综合训练） -->
        <el-form-item label="选择章节/小节" v-if="quizForm.practice_mode === 'chapter' || quizForm.practice_mode === 'random'">
          <el-cascader
            v-model="selectedCascaderValue"
            :options="cascaderOptions"
            :placeholder="quizForm.practice_mode === 'random' ? '请选择章节/节' : '请选择章节/小节'"
            :style="{ width: quizForm.practice_mode === 'random' ? '400px' : '850px', fontSize: '18px' }"
            :props="{ checkStrictly: quizForm.practice_mode === 'random' }" 
            @change="handleCascaderChange"
            clearable
          />
          <div v-if="quizForm.practice_mode === 'chapter' && !quizForm.subsection_id" style="color: #909399; font-size: 16px; margin-top: 8px; display: flex; align-items: center;">
            <el-icon style="margin-right: 4px;"><InfoFilled /></el-icon>
            请选择到具体小节后才可出题
          </div>
          <div v-if="quizForm.practice_mode === 'random' && !quizForm.section_id" style="color: #909399; font-size: 16px; margin-top: 8px; display: flex; align-items: center;">
            <el-icon style="margin-right: 4px;"><InfoFilled /></el-icon>
            请选择到具体节(Section)才可出题
          </div>
        </el-form-item>

        <!-- 单词训练模式开关 (已移除，默认启用) -->
        <!-- <el-form-item label="训练模式" v-if="quizForm.practice_mode === 'chapter' && quizForm.subsection_id"> ... </el-form-item> -->

        <!-- 题型选择（章节练习不显示，综合练习不显示） -->
        <el-form-item label="选择题型" v-if="quizForm.practice_mode !== 'chapter' && quizForm.practice_mode !== 'comprehensive' && quizForm.practice_mode !== 'random'">
           <template v-if="flatQuizOptions.length > 0">
             <el-select 
                v-model="selectedFlatType" 
                placeholder="请选择具体题型" 
                style="width: 250px;" 
                clearable
             >
               <el-option 
                  v-for="opt in flatQuizOptions" 
                  :key="opt.value" 
                  :label="opt.label" 
                  :value="opt.value" 
               >
                  <span style="float: left">{{ opt.label }}</span>
                  <span style="float: right; color: #8492a6; font-size: 13px; margin-left: 10px;">{{ opt.categoryLabel }}</span>
               </el-option>
             </el-select>
           </template>
           <template v-else>
             <span v-if="!quizForm.subsection_id && quizForm.practice_mode === 'chapter'" style="color: #909399; font-size: 12px; display: flex; align-items: center;">
                <el-icon style="margin-right: 4px;"><InfoFilled /></el-icon>
                请先选择章节具体小目标以解锁题型
             </span>
             <span v-else style="color: #909399; font-size: 12px; display: flex; align-items: center;">
                <el-icon style="margin-right: 4px;"><InfoFilled /></el-icon>
                该小节暂无特定题型要求，将进行智能综合练习
             </span>
           </template>
        </el-form-item>

        <!-- 难度选择（综合训练） -->
        <el-form-item label="难度" v-if="quizForm.practice_mode === 'random'">
           <el-select v-model="quizForm.difficulty" placeholder="请选择难度" style="width: 150px;">
              <el-option label="初级" value="初级" />
              <el-option label="中级" value="中级" />
              <el-option label="高级" value="高级" />
           </el-select>
        </el-form-item>

        <!-- 综合练习提示 -->
        <el-form-item v-if="quizForm.practice_mode === 'comprehensive'">
          <el-alert
            type="info"
            :closable="false"
            show-icon
            style="max-width: 500px;"
          >
            <template #title>
              <span style="font-size: 13px;">💡 推荐训练将根据AI学情分析的薄弱点自动分配题型</span>
            </template>
          </el-alert>
        </el-form-item>

        <el-form-item label="题数">
          <el-input-number v-model="quizForm.question_count" :min="1" :max="50" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleCreateQuiz" :loading="creating">
            开始练习
          </el-button>
        </el-form-item>
      </el-form>

      <el-divider />
      
      <el-row :gutter="20">
        <el-col :span="14">
          <h3 class="section-title">练习历史</h3>
          <el-table :data="quizHistory" style="width: 100%; font-size: 16px;" :row-style="{ height: '55px' }">
            <el-table-column prop="practice_mode" label="练习方式" width="120">
              <template #default="{ row }">
                <el-tag :type="getPracticeModeTagType(row.practice_mode)" size="default" effect="dark">
                  {{ getPracticeModeLabel(row.practice_mode) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="quiz_type" label="题型" width="220">
              <template #default="{ row }">
                <!-- 综合练习或混合题型：显示实际题型组合 -->
                <div v-if="(row.practice_mode === 'comprehensive' || row.quiz_type === 'mixed') && row.questions">
                  <template v-if="getQuestionTypes(row).length <= 2">
                    <!-- 2个或更少题型：直接全部显示 -->
                    <el-tag
                      v-for="type in getQuestionTypes(row)"
                      :key="type"
                      :type="getQuizTypeTagType(type)"
                      size="default"
                      style="margin-right: 4px; margin-bottom: 4px;"
                    >
                      {{ getQuizTypeLabel(type) }}
                    </el-tag>
                  </template>
                  <template v-else>
                    <!-- 超过2个题型：折叠显示 -->
                    <el-popover placement="top" :width="200" trigger="hover">
                      <template #reference>
                        <el-tag
                          :type="getQuizTypeTagType(getQuestionTypes(row)[0])"
                          size="default"
                          style="cursor: pointer;"
                        >
                          {{ getQuizTypeLabel(getQuestionTypes(row)[0]) }}
                          <span style="margin-left: 4px;">+{{ getQuestionTypes(row).length - 1 }}</span>
                        </el-tag>
                      </template>
                      <div>
                        <el-tag
                          v-for="type in getQuestionTypes(row)"
                          :key="type"
                          :type="getQuizTypeTagType(type)"
                          size="default"
                          style="margin-right: 4px; margin-bottom: 4px;"
                        >
                          {{ getQuizTypeLabel(type) }}
                        </el-tag>
                      </div>
                    </el-popover>
                  </template>
                </div>
                <!-- 其他练习方式：正常显示quiz_type -->
                <el-tag v-else :type="getQuizTypeTagType(row.quiz_type)" size="default">
                  {{ getQuizTypeLabel(row.quiz_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="score" label="分数" width="110">
              <template #default="{ row }">
                <span :style="{ color: row.score >= 60 ? '#67C23A' : '#F56C6C', fontWeight: 'bold', fontSize: '18px' }">
                  {{ row.score.toFixed(1) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="accuracy" label="正确率" width="110">
              <template #default="{ row }">
                <span style="font-weight: 500;">{{ row.accuracy.toFixed(1) }}%</span>
              </template>
            </el-table-column>
            <el-table-column prop="question_count" label="题数" width="80" align="center" />
            <el-table-column prop="time_spent" label="用时(秒)" width="100" align="center" />
            <el-table-column prop="created_at" label="时间" width="200">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.is_completed" type="success" size="default">已完成</el-tag>
                <el-tag v-else type="info" size="default">进行中</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right" align="center">
              <template #default="{ row }">
                <el-button 
                  v-if="row.practice_mode === 'comprehensive' || row.practice_mode === 'subsection'" 
                  type="primary" 
                  link 
                  size="default" 
                  style="font-size: 15px;" 
                  @click="handleViewRecommendedDetail(row.id)"
                >
                  查看详情
                </el-button>
                <el-button 
                  v-else
                  type="primary" 
                  link 
                  size="default" 
                  style="font-size: 15px;" 
                  @click="handleViewDetail(row.id)"
                >
                  查看详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-col>
        <el-col :span="10">
           <el-card shadow="hover" v-if="subsectionStats" class="stats-card">
              <template #header>
                <div class="stats-header">
                   <span class="stats-title-text">📊 小节数据分析</span>
                   <el-tag class="stats-subtitle-tag" type="primary" effect="light">{{ subsectionStats.subsection_title }}</el-tag>
                </div>
             </template>
              <div class="stats-content">
                 <!-- 顶部计数 -->
                 <div class="stats-overview">
                    <div class="overview-item">
                       <el-tooltip
                         v-if="subsectionStats.total_questions < (subsectionStats.min_questions || 10)"
                         class="box-item"
                         effect="dark"
                         :content="`做题数不足，最少需要 ${subsectionStats.min_questions || 10} 道题`"
                         placement="top"
                       >
                         <div class="overview-value error-text">
                            {{ subsectionStats.total_questions }}
                            <span class="min-req">/ {{ subsectionStats.min_questions || 10 }}</span>
                         </div>
                       </el-tooltip>
                       <div v-else class="overview-value success-text">
                          {{ subsectionStats.total_questions }}
                          <span class="min-req">/ {{ subsectionStats.min_questions || 10 }}</span>
                       </div>
                       <div class="overview-label">已做题数 (最少{{ subsectionStats.min_questions || 10 }})</div>
                    </div>
                    <div class="overview-divider"></div>
                    <div class="overview-item">
                       <div class="overview-value">{{ subsectionStats.total_quizzes }}</div>
                       <div class="overview-label">练习次数</div>
                    </div>
                 </div>
                 
                 <!-- 中间图表 -->
                 <div class="chart-wrapper">
                    <div ref="gaugeChartRef" class="gauge-chart"></div>
                 </div>

                 <!-- 底部最终得分 -->
                 <div class="final-score-card">
                    <div class="score-row">
                       <div class="score-col">
                          <div class="score-label">最终得分 <span class="weight-tag">权重 {{ subsectionStats.weight }}%</span></div>
                          
                          <el-tooltip
                             v-if="subsectionStats.total_questions < (subsectionStats.min_questions || 10)"
                             effect="dark"
                             :content="`请先完成最少 ${subsectionStats.min_questions || 10} 道题目以获取得分`"
                             placement="top"
                          >
                             <div class="score-value error-text">
                                -
                                <span class="score-sub">/ {{ subsectionStats.weight }}</span>
                             </div>
                          </el-tooltip>
                          
                          <div v-else class="score-value" :class="{ highlight: subsectionStats.final_score >= (subsectionStats.passing_score * subsectionStats.weight / 100) }">
                             {{ subsectionStats.final_score }}
                             <span class="score-sub">/ {{ subsectionStats.weight }}</span>
                          </div>
                       </div>
                       <div class="score-divider-vertical"></div>
                       <div class="score-col">
                          <div class="score-label">及格标准</div>
                          <div class="score-value pass-val">
                             {{ subsectionStats.passing_score }}
                             <span class="score-sub">分</span>
                          </div>
                       </div>
                    </div>
                 </div>
              </div>
           </el-card>

           <!-- 推荐训练薄弱点概览 -->
           <el-card shadow="hover" v-else-if="quizForm.practice_mode === 'comprehensive'" class="stats-card weak-points-overview">
              <template #header>
                <div class="stats-header">
                   <div class="header-title-group">
                      <el-icon class="header-icon" color="#E6A23C"><Warning /></el-icon>
                      <span>薄弱知识点详情</span>
                   </div>
                </div>
              </template>
              <div class="stats-content">
                  <div v-if="!weakPointsData || weakPointsData.length === 0" class="empty-state">
                      <el-empty description="暂无薄弱点数据，表现不错！" :image-size="80" />
                  </div>
                  <div v-else class="weak-points-list">
                      <el-collapse accordion>
                          <el-collapse-item v-for="(wp, index) in weakPointsData" :key="index" :name="index">
                              <template #title>
                                  <div class="wp-header">
                                      <span class="wp-title">{{ wp.knowledge_point_id }}</span>
                                      <el-tag :type="getSeverityType(wp.severity)" size="small" effect="plain" style="margin-left: auto;">
                                          {{ getSeverityText(wp.severity) }}
                                      </el-tag>
                                  </div>
                              </template>
                              <div class="wp-details">
                                  <div class="wp-stat-row">
                                      <span>平均分: <span :style="{ color: getScoreColor(wp.average_score) }">{{ wp.average_score }}</span></span>
                                      <span>薄弱点: {{ wp.weak_details ? wp.weak_details.length : 0 }}个</span>
                                  </div>
                                  
                                  <div v-if="wp.weak_details && wp.weak_details.length > 0" class="detail-list">
                                      <div v-for="(detail, idx) in wp.weak_details" :key="idx" class="detail-item">
                                          <div class="detail-content">
                                              <span class="detail-name">{{ detail.knowledge_point_id }}</span>
                                              <el-tag size="small">{{ detail.type }}</el-tag>
                                          </div>
                                          <div class="detail-metrics">
                                              <span>正确率: <span :style="{ color: getScoreColor(detail.accuracy) }">{{ detail.accuracy }}%</span></span>
                                              <span>错: {{ detail.error_count }}</span>
                                          </div>
                                      </div>
                                  </div>
                              </div>
                          </el-collapse-item>
                      </el-collapse>
                  </div>
              </div>
           </el-card>

           <el-card shadow="hover" v-else-if="overallStats && quizForm.practice_mode !== 'random'" class="stats-card sticky-card">
              <template #header>
                 <div class="stats-header">
                    <div class="header-title-group">
                       <el-icon class="header-icon"><DataAnalysis /></el-icon>
                       <span>章节总览</span>
                    </div>
                    <el-select 
                      v-model="selectedStatsChapter" 
                      placeholder="选择章节" 
                      size="large" 
                      style="width: 160px;"
                      class="chapter-select"
                      @change="handleStatsChapterChange"
                    >
                       <el-option
                         v-for="chapter in chapterOptions"
                         :key="chapter.value"
                         :label="chapter.label"
                         :value="chapter.value"
                       />
                    </el-select>
                 </div>
              </template>
              <div class="stats-content">
                 <!-- 如果有章节详细得分 breakdown -->
                 <div v-if="overallStats.chapter_score_breakdown">
                    <!-- 顶部总分展示 -->
                    <div class="chapter-total-score" :class="{ 'passed': overallStats.is_chapter_passed }">
                       <div class="score-circle">
                          <span class="score-num">{{ overallStats.total_chapter_score }}</span>
                          <span class="score-label">总分</span>
                       </div>
                       <div class="score-target">
                          目标: {{ overallStats.target_score }}分
                          <el-tag v-if="overallStats.is_chapter_passed" type="success" effect="dark">已达成</el-tag>
                          <el-tag v-else type="info" effect="plain">未达成</el-tag>
                       </div>
                    </div>

                    <!-- 小节列表 -->
                    <div class="subsection-stats-list">
                       <div v-for="sub in overallStats.chapter_score_breakdown" :key="sub.subsection_id" class="sub-stat-item">
                          <div class="sub-stat-header">
                             <span class="sub-title" :title="sub.subsection_title">{{ sub.subsection_title }}</span>
                             <el-tag size="small" type="info">{{ sub.weight }}%</el-tag>
                          </div>
                          <div class="sub-stat-body">
                             <div class="stat-row">
                                <span class="label">做题数:</span>
                                <span class="value" :class="{'error-text': sub.total_questions < sub.min_questions}">
                                   {{ sub.total_questions }}/{{ sub.min_questions }}
                                </span>
                             </div>
                             <div class="stat-row">
                                <span class="label">平均分:</span>
                                <span class="value" :class="{'success-text': sub.average_score >= sub.passing_score, 'error-text': sub.average_score < sub.passing_score}">
                                   {{ sub.average_score }}
                                   <span class="min-req" style="margin-left: 5px;">(及格分: {{ sub.passing_score }})</span>
                                </span>
                             </div>
                             <div class="stat-row">
                                <span class="label">得分:</span>
                                <span class="value score-val" :class="{'success-text': sub.final_score >= sub.weighted_passing_score, 'error-text': sub.final_score < sub.weighted_passing_score}">
                                   {{ sub.final_score }}
                                   <span class="min-req" style="margin-left: 5px; color: #909399; font-weight: normal;">(及格分: {{ sub.weighted_passing_score }})</span>
                                   <span v-if="sub.total_questions < sub.min_questions" class="status-tip">({{ sub.status_msg }})</span>
                                </span>
                             </div>
                          </div>
                          <el-progress 
                             :percentage="Math.min((sub.final_score / sub.weight) * 100, 100)" 
                             :status="sub.total_questions < sub.min_questions ? 'exception' : (sub.final_score >= (sub.weight * 0.6) ? 'success' : 'warning')"
                             :show-text="false"
                             :stroke-width="6"
                          />
                       </div>
                    </div>
                 </div>

                 <!-- 否则显示旧的统计视图 (兼容) -->
                 <div v-else>
                    <!-- 顶部计数 -->
                    <div class="stats-overview">
                       <div class="overview-item">
                          <div class="overview-value">{{ overallStats.total_questions }}</div>
                          <div class="overview-label">总做题数</div>
                       </div>
                       <div class="overview-divider"></div>
                       <div class="overview-item">
                          <div class="overview-value">{{ overallStats.completed_count }}</div>
                          <div class="overview-label">练习次数</div>
                       </div>
                    </div>
                    
                    <!-- 中间图表 -->
                    <div class="chart-wrapper">
                       <div ref="gaugeChartRef" class="gauge-chart"></div>
                    </div>

                    <!-- 底部平均正确率 -->
                    <div class="final-score-card">
                       <div class="score-row">
                          <div class="score-col">
                             <div class="score-label">平均正确率</div>
                             <div class="score-value highlight">
                                {{ overallStats.avg_accuracy }}
                                <span class="score-sub">%</span>
                             </div>
                          </div>
                          <div class="score-divider-vertical"></div>
                          <div class="score-col">
                             <div class="score-label">及格率</div>
                             <div class="score-value pass-val">
                                {{ overallStats.pass_rate }}
                                <span class="score-sub">%</span>
                             </div>
                          </div>
                       </div>
                    </div>
                 </div>
              </div>
           </el-card>

           <el-empty v-else description="请选择小节查看统计数据" image-size="100" />
        </el-col>
      </el-row>
    </el-card>

    <!-- 答题界面 -->
    <el-card v-else class="quiz-card">
      <template #header>
        <div style="display: flex; justify-content: space-between;">
          <span>
            <el-tag :type="getQuizTypeTagType(currentQuiz.quiz_type)" effect="dark">
              {{ getQuizTypeLabel(currentQuiz.quiz_type) }}
            </el-tag>
            <span style="margin-left: 10px;">共{{ questions.length }}题</span>
          </span>
          <span>
            <el-icon><Timer /></el-icon>
            已用时: <strong>{{ timeSpent }}</strong> 秒
          </span>
        </div>
      </template>

      <div v-for="(q, index) in questions" :key="index" class="question-item">
        <h4 class="question-title">
          <span class="question-number">{{ index + 1 }}.</span>
          <!-- 综合训练显示题型标签 -->
          <el-tag v-if="currentQuiz.practice_mode === 'comprehensive' || currentQuiz.quiz_type === 'mixed'" :type="getQuizTypeTagType(q.quiz_type)" size="small" style="margin-right: 10px">
            {{ getQuizTypeLabel(q.quiz_type) }}
          </el-tag>
          {{ q.question_text || q.question }}
        </h4>

        <!-- 通用音频播放器 (支持听写题等非Listening类型但有音频的题目) -->
        <div v-if="q.audio_url" class="audio-player-box">
          <h5>🎧 听力音频：</h5>
          <audio controls :src="getAudioUrl(q.audio_url)" class="audio-player">
            您的浏览器不支持音频播放。
          </audio>
        </div>

        <!-- 听力理解题 -->
        <div v-if="getQuestionType(q, currentQuiz.quiz_type) === 'listening'" class="listening-question">
          <!-- 听力选项 -->
          <div class="listening-options">
            <!-- 多选模式 (Options is Array) -->
            <div v-if="Array.isArray(q.options)">
                <p class="instruction-text">请勾选出你听到的单词（多选）：</p>
                <el-checkbox-group v-model="userAnswers[index]">
                  <el-checkbox 
                    v-for="(optText, i) in q.options" 
                    :key="i" 
                    :label="optText" 
                    border
                    style="margin-bottom: 10px; margin-right: 10px;"
                  >
                    {{ optText }}
                  </el-checkbox>
                </el-checkbox-group>
            </div>
            
            <!-- 单选模式 (Options is Object/Dict) -->
            <div v-else>
                <p class="instruction-text">请选择正确的单词（单选）：</p>
                <el-radio-group v-model="userAnswers[index]" class="answer-group horizontal-options">
                    <el-radio
                      v-for="(optText, optKey) in q.options"
                      :key="optKey"
                      :label="optKey"
                      class="answer-option horizontal-option"
                      border
                      style="margin-bottom: 10px; margin-right: 10px;"
                    >
                      <span class="option-key">{{ getOptionLabel(optKey) }}.</span>
                      <span class="option-text">{{ optText }}</span>
                    </el-radio>
                </el-radio-group>
            </div>
          </div>
        </div>

        <!-- 阅读理解题 -->
        <div v-if="getQuestionType(q, currentQuiz.quiz_type) === 'reading'" class="reading-question">
          <div class="passage-box">
            <h5>阅读材料：</h5>
            <p>{{ q.passage }}</p>
          </div>
          <el-radio-group
            v-model="userAnswers[index]"
            class="answer-group horizontal-options"
          >
            <el-radio
              v-for="(optText, optKey) in q.options"
              :key="optKey"
              :label="optKey"
              class="answer-option horizontal-option"
            >
              <span class="option-key">{{ getOptionLabel(optKey) }}.</span>
              <span class="option-text">{{ optText }}</span>
            </el-radio>
          </el-radio-group>
        </div>

        <!-- 词汇语法题 -->
        <div v-if="getQuestionType(q, currentQuiz.quiz_type) === 'vocabulary' || getQuestionType(q, currentQuiz.quiz_type) === 'choice'" class="vocabulary-question">
          <el-radio-group
            v-if="hasOptions(q)"
            v-model="userAnswers[index]"
            class="answer-group horizontal-options"
          >
            <el-radio
              v-for="(optText, optKey) in q.options"
              :key="optKey"
              :label="optKey"
              class="answer-option horizontal-option"
            >
              <span class="option-key">{{ getOptionLabel(optKey) }}.</span>
              <span class="option-text">{{ optText }}</span>
            </el-radio>
          </el-radio-group>
          <div v-else>
             <!-- 如果没有选项，显示输入框 (例如看中写英) -->
             <el-input
                v-model="userAnswers[index]"
                type="text"
                :rows="1"
                placeholder="请输入答案..."
                style="max-width: 400px;"
             />
          </div>
        </div>

        <!-- 单词训练题 (blank 类型) -->
        <div v-if="['blank', 'word_training', 'fill_in_the_blank', 'dictation', 'spelling'].includes(getQuestionType(q, currentQuiz.quiz_type))" class="vocabulary-question">
           <el-input
            v-model="userAnswers[index]"
            type="text"
            placeholder="请输入单词"
            style="max-width: 400px;"
          />
        </div>

        <!-- 翻译题 -->
        <div v-if="getQuestionType(q, currentQuiz.quiz_type) === 'translation'" class="translation-question">
          <div v-if="q.key_points && q.key_points.length > 0" class="key-points-box">
            <h5>翻译要点：</h5>
            <ul>
              <li v-for="(point, i) in q.key_points" :key="i">{{ point }}</li>
            </ul>
          </div>
          <el-input
            v-model="userAnswers[index]"
            type="textarea"
            :rows="4"
            placeholder="请输入英文翻译..."
          />
        </div>

        <!-- 写作题 -->
        <div v-if="getQuestionType(q, currentQuiz.quiz_type) === 'writing'" class="writing-question">
          <div class="writing-requirements">
            <h5>写作要求：</h5>
            <ul>
              <li v-for="(req, i) in q.requirements" :key="i">{{ req }}</li>
            </ul>
            <p><strong>字数要求：</strong>{{ q.word_count }}</p>
            <p v-if="q.reference_outline"><strong>参考提纲：</strong>{{ q.reference_outline }}</p>
          </div>
          <el-input
            v-model="userAnswers[index]"
            type="textarea"
            :rows="10"
            placeholder="请在此处写作..."
          />
        </div>
      </div>

      <div style="text-align: center; margin-top: 30px;">
        <el-button type="primary" size="large" @click="handleSubmit" :loading="submitting">
          提交答案
        </el-button>
        <el-button size="large" @click="handleCancel">
          取消
        </el-button>
      </div>
    </el-card>

    <!-- 结果对话框 -->
    <el-dialog v-model="showResult" title="练习结果" width="800px" :close-on-click-modal="false">
      <el-result
        :icon="result.accuracy >= 60 ? 'success' : 'warning'"
        :title="`得分: ${result.score?.toFixed(1) || 0}`"
      >
        <template #sub-title>
          <div class="result-stats">
            <div class="stat-item">
              <span class="stat-label">正确率</span>
              <span class="stat-value">{{ result.accuracy?.toFixed(1) || 0 }}%</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">正确题数</span>
              <span class="stat-value">{{ result.correct_count }} / {{ result.total_count }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">错题数</span>
              <span class="stat-value error">{{ result.wrong_count || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">用时</span>
              <span class="stat-value">{{ result.time_spent }}秒</span>
            </div>
          </div>
        </template>
        <template #extra>
          <el-button type="primary" @click="showDetailedResults = true">查看详细结果</el-button>
        </template>
      </el-result>

      <template #footer>
        <el-button type="primary" @click="handleRetry">再做一次</el-button>
        <el-button @click="() => { showResult = false; handleRetry() }">返回</el-button>
      </template>
    </el-dialog>

    <!-- 详细结果对话框 -->
    <el-dialog v-model="showDetailedResults" title="详细结果" width="900px">
      <div v-for="(item, index) in result.results" :key="index" class="result-item">
        <h4>
          <span>第{{ index + 1 }}题</span>
          <el-tag :type="item.is_correct ? 'success' : 'danger'" size="small">
            {{ item.is_correct ? '✓ 正确' : '✗ 错误' }}
          </el-tag>
          <span v-if="item.score !== undefined" class="score-badge">
            得分: {{ (item.score * 100).toFixed(0) }}分
          </span>
        </h4>

        <div class="result-content">
          <!-- 显示出题背景 (Meta Info) -->
          <div v-if="questions[item.question_index]?.meta" class="meta-info-box" style="margin-bottom: 15px;">
             <el-descriptions :column="1" size="small" border class="meta-descriptions">
                <el-descriptions-item label="🎯 出题知识">
                   <el-collapse accordion style="border: none;">
                      <el-collapse-item title="点击查看知识点内容" name="1">
                         <div class="knowledge-content">{{ questions[item.question_index].meta.word }}</div>
                      </el-collapse-item>
                   </el-collapse>
                </el-descriptions-item>
                <el-descriptions-item label="🤖 AI提示词">
                   <el-collapse accordion style="border: none;">
                      <el-collapse-item title="点击查看完整提示词" name="1">
                         <div class="prompt-content">{{ questions[item.question_index].meta.prompt }}</div>
                      </el-collapse-item>
                   </el-collapse>
                </el-descriptions-item>
             </el-descriptions>
          </div>

          <p><strong>你的答案：</strong>{{ formatAnswer(item.user_answer) }}</p>

          <!-- 写作题显示参考范文 -->
          <div v-if="questions[item.question_index]?.topic || questions[item.question_index]?.sample_essay">
            <p><strong>参考范文：</strong></p>
            <div class="sample-essay">
              {{ questions[item.question_index]?.sample_essay || questions[item.question_index]?.correct_answer }}
            </div>
          </div>
          <!-- 其他题型显示正确答案 -->
          <p v-else><strong>正确答案：</strong>{{ formatAnswer(item.correct_answer) }}</p>

          <div v-if="item.feedback" class="feedback">
            <strong>详细评语：</strong>
            <pre class="feedback-content">{{ item.feedback }}</pre>
          </div>

          <!-- 解析部分 - 分离显示答案解析和音频文本 -->
          <div v-if="item.explanation">
            <div v-if="item.explanation.includes('**音频文本：**')">
              <!-- 听力题：分离显示答案解析和音频文本 -->
              <div class="explanation">
                <strong>解析：</strong>{{ item.explanation.split('**音频文本：**')[0].trim() }}
              </div>
              <div class="audio-text-explanation">
                <strong>📝 音频文本：</strong>
                <pre class="audio-text-content">{{ item.explanation.split('**音频文本：**')[1].trim() }}</pre>
              </div>
            </div>
            <!-- 其他题型：正常显示 -->
            <p v-else class="explanation">
              <strong>解析：</strong>{{ item.explanation }}
            </p>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 历史练习详情对话框 -->
    <el-dialog v-model="showHistoryDetail" title="练习详情" width="1000px" :close-on-click-modal="false">
      <div v-if="historyDetail">
        <!-- 练习基本信息 -->
        <el-descriptions :column="3" border style="margin-bottom: 20px;">
          <el-descriptions-item label="题型">
            <el-tag :type="getQuizTypeTagType(historyDetail.quiz_type)">
              {{ getQuizTypeLabel(historyDetail.quiz_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="分数">
            <span :style="{ color: historyDetail.score >= 60 ? '#67C23A' : '#F56C6C', fontWeight: 'bold', fontSize: '18px' }">
              {{ historyDetail.score.toFixed(1) }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="正确率">
            {{ historyDetail.accuracy.toFixed(1) }}%
          </el-descriptions-item>
          <el-descriptions-item label="题目数量">
            {{ historyDetail.question_count }}
          </el-descriptions-item>
          <el-descriptions-item label="用时">
            {{ historyDetail.time_spent }}秒
          </el-descriptions-item>
          <el-descriptions-item label="完成时间">
            {{ historyDetail.completed_at ? formatDate(historyDetail.completed_at) : '未完成' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 题目和答题情况 -->
        <el-divider content-position="left">
          <h3>答题详情</h3>
        </el-divider>

        <div v-if="!historyDetail.is_completed" class="not-completed-hint">
          <el-alert type="info" :closable="false">
            此练习尚未完成，仅显示题目信息
          </el-alert>
        </div>

        <div v-for="(q, index) in historyQuestions" :key="index" class="history-question-item">
          <h4 class="question-title">
            <span class="question-number">{{ index + 1 }}.</span>
            <!-- 综合训练显示题型标签 -->
            <el-tag v-if="historyDetail.practice_mode === 'comprehensive' || historyDetail.quiz_type === 'mixed'" :type="getQuizTypeTagType(q.quiz_type)" size="small" style="margin-right: 10px">
              {{ getQuizTypeLabel(q.quiz_type) }}
            </el-tag>
            {{ q.question_text || q.question }}
            <el-tag
              v-if="historyDetail.is_completed && historyUserAnswers[index] !== undefined"
              :type="isHistoryAnswerCorrect(index) ? 'success' : 'danger'"
              size="small"
              style="margin-left: 10px;"
            >
              {{ isHistoryAnswerCorrect(index) ? '✓ 正确' : '✗ 错误' }}
            </el-tag>
          </h4>

          <div v-if="q.meta" class="meta-info-box">
             <el-descriptions :column="1" size="small" border class="meta-descriptions">
                <el-descriptions-item label="🎯 出题知识">
                   <el-collapse accordion style="border: none;">
                      <el-collapse-item title="点击查看知识点内容" name="1">
                         <div class="knowledge-content">{{ q.meta.word }}</div>
                      </el-collapse-item>
                   </el-collapse>
                </el-descriptions-item>
                <el-descriptions-item label="🤖 AI提示词">
                   <el-collapse accordion style="border: none;">
                      <el-collapse-item title="点击查看完整提示词" name="1">
                         <div class="prompt-content">{{ q.meta.prompt }}</div>
                      </el-collapse-item>
                   </el-collapse>
                </el-descriptions-item>
             </el-descriptions>
          </div>

          <!-- 通用音频播放器 (支持听力题、听写题等) -->
          <div v-if="q.audio_url || q.audio_text" class="audio-player-box" style="margin-bottom: 15px;">
             <div v-if="q.audio_url">
                <h5>🎧 听力音频：</h5>
                <audio controls :src="getAudioUrl(q.audio_url)" class="audio-player">
                  您的浏览器不支持音频播放。
                </audio>
             </div>
             <!-- 降级方案：如果没有音频URL，显示音频文本 -->
             <div v-else-if="q.audio_text" class="audio-text-box">
                <h5>听力材料：</h5>
                <p>{{ q.audio_text }}</p>
             </div>
          </div>

          <!-- 听力、阅读、选择、词汇 -->
          <div v-if="['listening', 'reading', 'choice', 'vocabulary'].includes(getQuestionType(q, historyDetail.quiz_type))" class="answer-display">
            <!-- 听力题显示音频播放器 (已移至通用显示区域，此处移除以免重复) -->
            <!-- 阅读题显示阅读材料 -->
            <div v-if="getQuestionType(q, historyDetail.quiz_type) === 'reading' && q.passage" class="passage-box">
              <h5>阅读材料：</h5>
              <p>{{ q.passage }}</p>
            </div>
            
            <!-- 选择题选项显示 (单选/字典格式选项) -->
            <div v-if="q.options && !Array.isArray(q.options)">
              <div v-for="(optText, optKey) in q.options" :key="optKey" class="option-item">
                <span :class="['option-label', {
                  'correct-option': optKey === q.correct_answer,
                  'user-option': historyDetail.is_completed && optKey === historyUserAnswers[index],
                  'wrong-option': historyDetail.is_completed && optKey === historyUserAnswers[index] && optKey !== q.correct_answer
                }]">
                  <span class="option-key-history">{{ getOptionLabel(optKey) }}.</span>
                  <span class="option-text-history">{{ optText }}</span>
                </span>
              </div>
            </div>

            <!-- 听力多选结果显示 (列表格式选项) -->
            <div v-else-if="getQuestionType(q, historyDetail.quiz_type) === 'listening' && Array.isArray(q.options)" class="listening-result-box">
              <div class="result-item">
                <p class="label"><strong>你的选择：</strong></p>
                <div class="word-list">
                  <el-tag 
                    v-for="(word, i) in (Array.isArray(historyUserAnswers[index]) ? historyUserAnswers[index] : [])" 
                    :key="i"
                    :type="q.correct_answer.includes(word) ? 'success' : 'danger'"
                    style="margin-right: 5px; margin-bottom: 5px;"
                  >
                    {{ word }}
                  </el-tag>
                  <span v-if="!historyUserAnswers[index] || historyUserAnswers[index].length === 0">未作答</span>
                </div>
              </div>
              <div class="result-item" style="margin-top: 15px;">
                <p class="label"><strong>正确答案：</strong></p>
                <div class="word-list">
                   <el-tag 
                    v-for="(word, i) in q.correct_answer" 
                    :key="i"
                    type="success"
                    effect="dark"
                    style="margin-right: 5px; margin-bottom: 5px;"
                  >
                    {{ word }}
                  </el-tag>
                </div>
              </div>
            </div>

            <!-- 详细评语和分数 (如有) -->
            <div v-if="historyResults[index] && (historyResults[index].feedback || historyResults[index].score !== undefined)" class="feedback-section" style="margin-top: 15px; padding-top: 10px; border-top: 1px dashed #eee;">
               <div v-if="historyResults[index].feedback" class="feedback-box">
                  <strong>详细评语：</strong>
                  <div class="feedback-text">{{ historyResults[index].feedback }}</div>
               </div>
            </div>
          </div>

          <!-- 填空题 (默写/单词训练) -->
          <div v-else-if="['blank', 'word_training', 'fill_in_the_blank', 'dictation', 'spelling'].includes(getQuestionType(q, historyDetail.quiz_type))" class="answer-display">
              <div v-if="historyDetail.is_completed">
                  <p><strong>你的答案：</strong>
                    <span :class="{'text-success': isHistoryAnswerCorrect(index), 'text-danger': !isHistoryAnswerCorrect(index)}" style="font-weight: bold;">
                        {{ historyUserAnswers[index] || '未作答' }}
                    </span>
                  </p>
                  <p><strong>正确答案：</strong><span class="text-success" style="font-weight: bold;">{{ q.correct_answer }}</span></p>
                  
                  <!-- 详细评语 -->
                  <div v-if="historyResults[index] && historyResults[index].feedback" class="feedback-box" style="margin-top: 10px;">
                      <strong>详细评语：</strong>
                      <div class="feedback-text">{{ historyResults[index].feedback }}</div>
                  </div>
              </div>
              <div v-else>
                  <p><strong>正确答案：</strong>{{ q.correct_answer }}</p>
              </div>
          </div>

          <!-- 翻译题 -->
          <div v-else-if="getQuestionType(q, historyDetail.quiz_type) === 'translation'" class="answer-display">
            <div v-if="q.key_points && q.key_points.length > 0" class="key-points-box">
              <h5>翻译要点：</h5>
              <ul>
                <li v-for="(point, i) in q.key_points" :key="i">{{ point }}</li>
              </ul>
            </div>
            <div v-if="historyDetail.is_completed">
              <p><strong>你的翻译：</strong>{{ historyUserAnswers[index] || '未作答' }}</p>
              <p><strong>参考翻译：</strong>{{ q.correct_answer }}</p>
            </div>
            <div v-else>
              <p><strong>参考翻译：</strong>{{ q.correct_answer }}</p>
            </div>
          </div>

          <!-- 写作题 -->
          <div v-else-if="getQuestionType(q, historyDetail.quiz_type) === 'writing'" class="answer-display">
            <div class="writing-requirements">
              <h5>写作要求：</h5>
              <ul>
                <li v-for="(req, i) in q.requirements" :key="i">{{ req }}</li>
              </ul>
              <p><strong>字数要求：</strong>{{ q.word_count }}</p>
              <p v-if="q.reference_outline"><strong>参考提纲：</strong>{{ q.reference_outline }}</p>
            </div>
            <div v-if="historyDetail.is_completed">
              <p><strong>你的作文：</strong></p>
              <div class="user-writing">{{ historyUserAnswers[index] || '未作答' }}</div>

              <!-- 显示评分和反馈 -->
              <div v-if="historyResults[index]" style="margin-top: 20px;">
                <el-divider />
                <div style="margin-bottom: 15px;">
                  <el-tag :type="historyResults[index].is_correct ? 'success' : 'warning'" size="large">
                    得分: {{ (historyResults[index].score * 100).toFixed(0) }}分
                  </el-tag>
                </div>
                <div v-if="historyResults[index].feedback" class="feedback-box">
                  <strong>详细评语：</strong>
                  <pre class="feedback-text">{{ historyResults[index].feedback }}</pre>
                </div>
              </div>

              <!-- 显示参考范文 -->
              <div v-if="q.sample_essay || q.correct_answer" style="margin-top: 20px;">
                <p><strong>参考范文：</strong></p>
                <div class="sample-essay">{{ q.sample_essay || q.correct_answer }}</div>
              </div>
            </div>
            <div v-else>
              <!-- 未完成时也显示参考范文 -->
              <div v-if="q.sample_essay || q.correct_answer">
                <p><strong>参考范文：</strong></p>
                <div class="sample-essay">{{ q.sample_essay || q.correct_answer }}</div>
              </div>
            </div>
          </div>

          <!-- 答案解析 - 分离显示答案解析和音频文本 -->
          <div v-if="q.explanation">
            <div v-if="q.explanation.includes('**音频文本：**')">
              <!-- 听力题：分离显示答案解析和音频文本 -->
              <div class="explanation-box">
                <strong>解析：</strong>{{ q.explanation.split('**音频文本：**')[0].trim() }}
              </div>
              <div class="audio-text-explanation">
                <strong>📝 音频文本：</strong>
                <pre class="audio-text-content">{{ q.explanation.split('**音频文本：**')[1].trim() }}</pre>
              </div>
            </div>
            <!-- 其他题型：正常显示 -->
            <div v-else class="explanation-box">
              <strong>解析：</strong>{{ q.explanation }}
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 推荐训练历史练习详情对话框 (独立) -->
    <el-dialog v-model="showRecommendedHistoryDetail" title="推荐训练详情" width="1000px" :close-on-click-modal="false" class="recommended-detail-dialog">
      <div v-if="recommendedHistoryDetail">
        <!-- 练习基本信息 -->
        <el-descriptions :column="3" border style="margin-bottom: 20px;">
          <el-descriptions-item label="题型">
            <el-tag :type="getQuizTypeTagType(recommendedHistoryDetail.quiz_type)">
              {{ getQuizTypeLabel(recommendedHistoryDetail.quiz_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="分数">
            <span :style="{ color: recommendedHistoryDetail.score >= 60 ? '#67C23A' : '#F56C6C', fontWeight: 'bold', fontSize: '18px' }">
              {{ recommendedHistoryDetail.score.toFixed(1) }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="正确率">
            {{ recommendedHistoryDetail.accuracy.toFixed(1) }}%
          </el-descriptions-item>
          <el-descriptions-item label="题目数量">
            {{ recommendedHistoryDetail.question_count }}
          </el-descriptions-item>
          <el-descriptions-item label="用时">
            {{ recommendedHistoryDetail.time_spent }}秒
          </el-descriptions-item>
          <el-descriptions-item label="完成时间">
            {{ recommendedHistoryDetail.completed_at ? formatDate(recommendedHistoryDetail.completed_at) : '未完成' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 题目和答题情况 -->
        <el-divider content-position="left">
          <h3>答题详情 (推荐训练)</h3>
        </el-divider>

        <div v-if="!recommendedHistoryDetail.is_completed" class="not-completed-hint">
          <el-alert type="info" :closable="false">
            此练习尚未完成，仅显示题目信息
          </el-alert>
        </div>

        <div v-for="(q, index) in recommendedHistoryQuestions" :key="index" class="history-question-item recommended-item">
          <h4 class="question-title">
            <span class="question-number">{{ index + 1 }}.</span>
            <!-- 综合训练显示题型标签 -->
            <el-tag v-if="recommendedHistoryDetail.practice_mode === 'comprehensive' || recommendedHistoryDetail.quiz_type === 'mixed'" :type="getQuizTypeTagType(q.quiz_type)" size="small" style="margin-right: 10px">
              {{ getQuizTypeLabel(q.quiz_type) }}
            </el-tag>
            {{ q.question_text || q.question }}
            <el-tag
              v-if="recommendedHistoryDetail.is_completed && recommendedHistoryUserAnswers[index] !== undefined"
              :type="isRecommendedHistoryAnswerCorrect(index) ? 'success' : 'danger'"
              size="small"
              style="margin-left: 10px;"
            >
              {{ isRecommendedHistoryAnswerCorrect(index) ? '✓ 正确' : '✗ 错误' }}
            </el-tag>
          </h4>

          <div v-if="q.meta" class="meta-info-box">
             <el-descriptions :column="1" size="small" border class="meta-descriptions">
                <el-descriptions-item label="🎯 出题知识">
                   <el-collapse accordion style="border: none;">
                      <el-collapse-item title="点击查看知识点内容" name="1">
                         <div class="knowledge-content">{{ q.meta.word }}</div>
                      </el-collapse-item>
                   </el-collapse>
                </el-descriptions-item>
                <el-descriptions-item label="🤖 AI提示词">
                   <el-collapse accordion style="border: none;">
                      <el-collapse-item title="点击查看完整提示词" name="1">
                         <div class="prompt-content">{{ q.meta.prompt }}</div>
                      </el-collapse-item>
                   </el-collapse>
                </el-descriptions-item>
             </el-descriptions>
          </div>

          <!-- 通用音频播放器 (支持听力题、听写题等) -->
          <div v-if="q.audio_url || q.audio_text" class="audio-player-box" style="margin-bottom: 15px;">
             <div v-if="q.audio_url">
                <h5>🎧 听力音频：</h5>
                <audio controls :src="getAudioUrl(q.audio_url)" class="audio-player">
                  您的浏览器不支持音频播放。
                </audio>
             </div>
             <!-- 降级方案：如果没有音频URL，显示音频文本 -->
             <div v-else-if="q.audio_text" class="audio-text-box">
                <h5>听力材料：</h5>
                <p>{{ q.audio_text }}</p>
             </div>
          </div>

          <!-- 听力、阅读、选择、词汇 -->
          <div v-if="['listening', 'reading', 'choice', 'vocabulary'].includes(getQuestionType(q, recommendedHistoryDetail.quiz_type))" class="answer-display">
            <!-- 听力题显示音频播放器 (已移至通用显示区域，此处移除以免重复) -->
            <!-- 阅读题显示阅读材料 -->
            <div v-if="getQuestionType(q, recommendedHistoryDetail.quiz_type) === 'reading' && q.passage" class="passage-box">
              <h5>阅读材料：</h5>
              <p>{{ q.passage }}</p>
            </div>
            
            <!-- 选择题选项显示 (单选/字典格式选项) -->
            <div v-if="q.options && !Array.isArray(q.options)">
              <div v-for="(optText, optKey) in q.options" :key="optKey" class="option-item">
                <span :class="['option-label', {
                  'correct-option': optKey === q.correct_answer,
                  'user-option': recommendedHistoryDetail.is_completed && optKey === recommendedHistoryUserAnswers[index],
                  'wrong-option': recommendedHistoryDetail.is_completed && optKey === recommendedHistoryUserAnswers[index] && optKey !== q.correct_answer
                }]">
                  <span class="option-key-history">{{ getOptionLabel(optKey) }}.</span>
                  <span class="option-text-history">{{ optText }}</span>
                </span>
              </div>
            </div>

            <!-- 听力多选结果显示 (列表格式选项) -->
            <div v-else-if="getQuestionType(q, recommendedHistoryDetail.quiz_type) === 'listening' && Array.isArray(q.options)" class="listening-result-box">
              <div class="result-item">
                <p class="label"><strong>你的选择：</strong></p>
                <div class="word-list">
                  <el-tag 
                    v-for="(word, i) in (Array.isArray(recommendedHistoryUserAnswers[index]) ? recommendedHistoryUserAnswers[index] : [])" 
                    :key="i"
                    :type="q.correct_answer.includes(word) ? 'success' : 'danger'"
                    style="margin-right: 5px; margin-bottom: 5px;"
                  >
                    {{ word }}
                  </el-tag>
                  <span v-if="!recommendedHistoryUserAnswers[index] || recommendedHistoryUserAnswers[index].length === 0">未作答</span>
                </div>
              </div>
              <div class="result-item" style="margin-top: 15px;">
                <p class="label"><strong>正确答案：</strong></p>
                <div class="word-list">
                   <el-tag 
                    v-for="(word, i) in q.correct_answer" 
                    :key="i"
                    type="success"
                    effect="dark"
                    style="margin-right: 5px; margin-bottom: 5px;"
                  >
                    {{ word }}
                  </el-tag>
                </div>
              </div>
            </div>

            <!-- 详细评语和分数 (如有) -->
            <div v-if="recommendedHistoryResults[index] && (recommendedHistoryResults[index].feedback || recommendedHistoryResults[index].score !== undefined)" class="feedback-section" style="margin-top: 15px; padding-top: 10px; border-top: 1px dashed #eee;">
               <div v-if="recommendedHistoryResults[index].feedback" class="feedback-box">
                  <strong>详细评语：</strong>
                  <div class="feedback-text">{{ recommendedHistoryResults[index].feedback }}</div>
               </div>
            </div>
          </div>

          <!-- 填空题 (默写/单词训练) -->
          <div v-else-if="['blank', 'word_training', 'fill_in_the_blank', 'dictation', 'spelling'].includes(getQuestionType(q, recommendedHistoryDetail.quiz_type))" class="answer-display">
              <div v-if="recommendedHistoryDetail.is_completed">
                  <p><strong>你的答案：</strong>
                    <span :class="{'text-success': isRecommendedHistoryAnswerCorrect(index), 'text-danger': !isRecommendedHistoryAnswerCorrect(index)}" style="font-weight: bold;">
                        {{ recommendedHistoryUserAnswers[index] || '未作答' }}
                    </span>
                  </p>
                  <p><strong>正确答案：</strong><span class="text-success" style="font-weight: bold;">{{ q.correct_answer }}</span></p>
                  
                  <!-- 详细评语 -->
                  <div v-if="recommendedHistoryResults[index] && recommendedHistoryResults[index].feedback" class="feedback-box" style="margin-top: 10px;">
                      <strong>详细评语：</strong>
                      <div class="feedback-text">{{ recommendedHistoryResults[index].feedback }}</div>
                  </div>
              </div>
              <div v-else>
                  <p><strong>正确答案：</strong>{{ q.correct_answer }}</p>
              </div>
          </div>

          <!-- 翻译题 -->
          <div v-else-if="getQuestionType(q, recommendedHistoryDetail.quiz_type) === 'translation'" class="answer-display">
            <div v-if="q.key_points && q.key_points.length > 0" class="key-points-box">
              <h5>翻译要点：</h5>
              <ul>
                <li v-for="(point, i) in q.key_points" :key="i">{{ point }}</li>
              </ul>
            </div>
            <div v-if="recommendedHistoryDetail.is_completed">
              <p><strong>你的翻译：</strong>{{ recommendedHistoryUserAnswers[index] || '未作答' }}</p>
              <p><strong>参考翻译：</strong>{{ q.correct_answer }}</p>
            </div>
            <div v-else>
              <p><strong>参考翻译：</strong>{{ q.correct_answer }}</p>
            </div>
          </div>

          <!-- 写作题 -->
          <div v-else-if="getQuestionType(q, recommendedHistoryDetail.quiz_type) === 'writing'" class="answer-display">
            <div class="writing-requirements">
              <h5>写作要求：</h5>
              <ul>
                <li v-for="(req, i) in q.requirements" :key="i">{{ req }}</li>
              </ul>
              <p><strong>字数要求：</strong>{{ q.word_count }}</p>
              <p v-if="q.reference_outline"><strong>参考提纲：</strong>{{ q.reference_outline }}</p>
            </div>
            <div v-if="recommendedHistoryDetail.is_completed">
              <p><strong>你的作文：</strong></p>
              <div class="user-writing">{{ recommendedHistoryUserAnswers[index] || '未作答' }}</div>

              <!-- 显示评分和反馈 -->
              <div v-if="recommendedHistoryResults[index]" style="margin-top: 20px;">
                <el-divider />
                <div style="margin-bottom: 15px;">
                  <el-tag :type="recommendedHistoryResults[index].is_correct ? 'success' : 'warning'" size="large">
                    得分: {{ (recommendedHistoryResults[index].score * 100).toFixed(0) }}分
                  </el-tag>
                </div>
                <div v-if="recommendedHistoryResults[index].feedback" class="feedback-box">
                  <strong>详细评语：</strong>
                  <pre class="feedback-text">{{ recommendedHistoryResults[index].feedback }}</pre>
                </div>
              </div>

              <!-- 显示参考范文 -->
              <div v-if="q.sample_essay || q.correct_answer" style="margin-top: 20px;">
                <p><strong>参考范文：</strong></p>
                <div class="sample-essay">{{ q.sample_essay || q.correct_answer }}</div>
              </div>
            </div>
            <div v-else>
              <!-- 未完成时也显示参考范文 -->
              <div v-if="q.sample_essay || q.correct_answer">
                <p><strong>参考范文：</strong></p>
                <div class="sample-essay">{{ q.sample_essay || q.correct_answer }}</div>
              </div>
            </div>
          </div>

          <!-- 答案解析 - 分离显示答案解析和音频文本 -->
          <div v-if="q.explanation">
            <div v-if="q.explanation.includes('**音频文本：**')">
              <!-- 听力题：分离显示答案解析和音频文本 -->
              <div class="explanation-box">
                <strong>解析：</strong>{{ q.explanation.split('**音频文本：**')[0].trim() }}
              </div>
              <div class="audio-text-explanation">
                <strong>📝 音频文本：</strong>
                <pre class="audio-text-content">{{ q.explanation.split('**音频文本：**')[1].trim() }}</pre>
              </div>
            </div>
            <!-- 其他题型：正常显示 -->
            <div v-else class="explanation-box">
              <strong>解析：</strong>{{ q.explanation }}
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { createPersonalizedQuiz, createQuiz, createSectionComprehensiveQuiz, generateWordTraining, getMyLearningAnalysis, getQuiz, getQuizHistory, getQuizStats, getSubsectionStats, submitQuiz } from '@/api'
import { useChapterStore } from '@/stores'
import { DataAnalysis, Loading, Timer } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { ElMessage, ElNotification } from 'element-plus'
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const chapterStore = useChapterStore()
const creating = ref(false)
// const isWordTraining = ref(false) // Removed: Word Training Mode switch
const submitting = ref(false)
const showResult = ref(false)
const showDetailedResults = ref(false)
const showHistoryDetail = ref(false)
const showRecommendedHistoryDetail = ref(false) // 推荐训练独立详情弹窗
const currentQuiz = ref<any>(null)
const questions = ref<any[]>([])
const userAnswers = ref<any[]>([])
const timeSpent = ref(0)
const quizHistory = ref<any[]>([])
const result = ref<any>({})
const historyDetail = ref<any>(null)
const historyQuestions = ref<any[]>([])
const historyUserAnswers = ref<any[]>([])
const historyCorrectAnswers = ref<any[]>([])
const historyResults = ref<any[]>([])  // 详细批改结果

// 推荐训练独立的状态变量
const recommendedHistoryDetail = ref<any>(null)
const recommendedHistoryQuestions = ref<any[]>([])
const recommendedHistoryUserAnswers = ref<any[]>([])
const recommendedHistoryCorrectAnswers = ref<any[]>([])
const recommendedHistoryResults = ref<any[]>([])
const loadingText = ref('正在出题中...')
const loadingSubText = ref('AI正在为你精心准备题目，请稍候')
const loadingProgress = ref(0)
const sourceDocumentsInfo = ref<any[]>([])
const sourceChunksInfo = ref<any[]>([])
const ragContextPreview = ref<string>('')
const rulesPreview = ref<string>('')
let timer: any = null

const subsectionStats = ref<any>(null)
const overallStats = ref<any>(null)
const weakPointsData = ref<any[]>([]) // 新增：薄弱知识点数据
const selectedStatsChapter = ref<number | null>(null) // 新增：用于统计卡片的章节选择
const gaugeChartRef = ref<HTMLElement | null>(null)
let gaugeChart: echarts.ECharts | null = null

const quizForm = reactive({
  practice_mode: 'chapter' as 'chapter' | 'random' | 'comprehensive',  // 练习方式
  chapter_id: 0,
  section_id: undefined as number | undefined, // 新增：节ID
  subsection_id: undefined as number | undefined, // 新增：小节ID
  quiz_type: 'listening' as any,
  question_count: 5,
  difficulty: 'intermediate'
})

// 级联选择器的绑定值
const selectedCascaderValue = ref<any[]>([])

// 级联选择器选项
const cascaderOptions = computed(() => {
  return chapterStore.chapters.map((chapter: any) => {
    // 基础结构：章
    const option: any = {
      value: chapter.id,
      label: `第${chapter.chapter_number}章 ${chapter.title}`,
      level: 'chapter',
      children: []
    }

    if (chapter.sections) {
      option.children = chapter.sections.map((section: any) => {
        // 基础结构：节
        const sectionOption: any = {
          value: section.id,
          label: section.title,
          level: 'section'
        }

        // 仅在非综合训练模式下（即章节练习）添加小节
        // 综合训练 (random) 只需要到 Section 级别
        if (quizForm.practice_mode !== 'random' && section.subsections) {
          sectionOption.children = section.subsections.map((sub: any) => ({
            value: sub.id,
            label: sub.title,
            level: 'subsection',
            requirements: sub.requirements
          }))
        }
        
        return sectionOption
      })
    }
    
    return option
  })
})

// 章节选择下拉框选项 (用于统计卡片)
const chapterOptions = computed(() => {
  return chapterStore.chapters.map((chapter: any) => ({
    value: chapter.id,
    label: `第${chapter.chapter_number}章`
  }))
})

// 监听级联选择器变化
  const handleCascaderChange = async (value: any[]) => {
    if (!value || value.length === 0) {
      quizForm.chapter_id = 0
      quizForm.section_id = undefined
      quizForm.subsection_id = undefined
      subsectionStats.value = null
      
      // 只有非综合训练模式下才显示整体统计
      if (quizForm.practice_mode !== 'random') {
        fetchOverallStats() 
      }
      return
    }

  // 更新 chapter_id (总是取第一级)
  quizForm.chapter_id = value[0]
  
  // 更新 section_id (如果有第二级)
  if (value.length >= 2) {
      quizForm.section_id = value[1]
  } else {
      quizForm.section_id = undefined
  }
  
  // 如果选到了小目标（第三级）
  if (value.length === 3) {
    quizForm.subsection_id = value[2]
    
    // 查找选中的 subsection 对象以获取 requirements
    const chapter = chapterStore.chapters.find((c: any) => c.id === value[0])
    const section = chapter?.sections?.find((s: any) => s.id === value[1])
    const subsection = section?.subsections?.find((sub: any) => sub.id === value[2])
    
    if (subsection && subsection.requirements) {
      parseRequirementsAndSetType(subsection.requirements)
    }

    // 获取小节统计数据
    await fetchSubsectionStatsData(value[2])
  } else {
    quizForm.subsection_id = undefined
    subsectionStats.value = null
    // fetchOverallStats() // Keep current stats or fetch overall?
  }
}

const fetchSubsectionStatsData = async (subsectionId: number) => {
  try {
    const res = await getSubsectionStats(subsectionId)
    subsectionStats.value = res
    nextTick(() => {
      initGaugeChart(res.average_score, '平均分', res.passing_score)
    })
  } catch (error) {
    console.error('Failed to fetch subsection stats:', error)
    subsectionStats.value = null
  }
}

const fetchOverallStats = async (explicitChapterId?: number) => {
  try {
    const chapterId = explicitChapterId ?? selectedStatsChapter.value
    // Pass chapterId to getQuizStats if selected
    const res: any = await getQuizStats(chapterId)
    overallStats.value = res
    
    // Determine title based on chapter selection
    const title = '平均分'
    
    nextTick(() => {
      initGaugeChart(res.avg_score, title, 60)
    })
  } catch (error) {
    console.error('Failed to fetch overall stats:', error)
    overallStats.value = null
  }
}

const handleStatsChapterChange = (val: any) => {
  console.log('Chapter changed to:', val)
  fetchOverallStats(val)
}

// 获取薄弱知识点数据（用于推荐训练）
const fetchWeakPointsData = async () => {
  try {
    const res: any = await getMyLearningAnalysis()
    if (res && res.data && res.data.weak_points) {
      weakPointsData.value = res.data.weak_points
    } else {
      weakPointsData.value = []
    }
  } catch (e) {
    console.error('Failed to fetch weak points:', e)
    weakPointsData.value = []
  }
}

// 获取分数颜色
const getScoreColor = (score: number): string => {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

// 获取严重程度类型
const getSeverityType = (severity: string): 'danger' | 'warning' | 'success' => {
  switch (severity) {
    case 'high':
      return 'danger'
    case 'medium':
      return 'warning'
    default:
      return 'success'
  }
}

// 获取严重程度文本
const getSeverityText = (severity: string): string => {
  switch (severity) {
    case 'high':
      return '严重'
    case 'medium':
      return '中等'
    default:
      return '轻微'
  }
}

const initGaugeChart = (score: number, title: string, passingScore: number = 60) => {
  if (!gaugeChartRef.value) return
  
  // Dispose existing chart if any to avoid memory leaks or conflicts
  if (gaugeChart) {
    gaugeChart.dispose()
  }

  gaugeChart = echarts.init(gaugeChartRef.value)
  
  const option = {
    series: [
      {
        type: 'gauge',
        startAngle: 180,
        endAngle: 0,
        min: 0,
        max: 100,
        radius: '115%',
        center: ['50%', '70%'], // Enlarged and moved down
        splitNumber: 5,
        itemStyle: {
          // Dynamic pointer color based on passing score
          color: score >= passingScore ? '#67C23A' : '#F56C6C',
          shadowColor: 'rgba(0,138,255,0.45)',
          shadowBlur: 10,
          shadowOffsetX: 2,
          shadowOffsetY: 2
        },
        progress: {
          show: true,
          roundCap: true,
          width: 25
        },
        pointer: {
          icon: 'path://M2090.36389,615.30999 L2090.36389,615.30999 C2091.48372,615.30999 2092.40383,616.194028 2092.44859,617.312956 L2096.90698,728.755929 C2100.13176,809.343567 2136.42152,881.340576 2189.78912,933.268065 L2189.78912,933.268065 C2190.49529,933.95519 2190.49529,935.111818 2189.78912,935.798943 L2189.78912,935.798943 C2183.13627,942.270561 2175.76019,948.064563 2167.7554,953.078972 C2150.38096,963.962295 2129.83733,970.218841 2107.83038,970.218841 C2085.82343,970.218841 2065.27981,963.962295 2047.90536,953.078972 C2039.90057,948.064563 2032.52449,942.270561 2025.87164,935.798943 L2025.87164,935.798943 C2025.16547,935.111818 2025.16547,933.95519 2025.87164,933.268065 L2025.87164,933.268065 C2079.23924,881.340576 2115.529,809.343567 2118.75378,728.755929 L2123.21217,617.312956 C2123.25693,616.194028 2124.17704,615.30999 2125.29687,615.30999 Z',
          length: '65%',
          width: 15,
          offsetCenter: [0, '5%']
        },
        axisLine: {
          roundCap: true,
          lineStyle: {
            width: 25,
            // Dynamic axis color based on passing score
            color: [
              [passingScore / 100, '#F56C6C'], // Red for failing range
              [1, '#67C23A']  // Green for passing range
            ]
          }
        },
        axisTick: {
          splitNumber: 2,
          lineStyle: {
            width: 2,
            color: '#999'
          }
        },
        splitLine: {
          length: 30,
          lineStyle: {
            width: 3,
            color: '#999'
          }
        },
        axisLabel: {
          distance: 40,
          color: '#999',
          fontSize: 14
        },
        title: {
          show: true,
          offsetCenter: [0, '-30%'], // Moved up to clear needle and labels
          fontSize: 24,
          fontWeight: 'bold',
          color: '#303133' // Ensure visibility
        },
        detail: {
          backgroundColor: '#fff',
          borderColor: '#999',
          borderWidth: 2,
          width: '50%',
          lineHeight: 50,
          height: 50,
          borderRadius: 8,
          offsetCenter: [0, '25%'], // Moved closer to the center
          valueAnimation: true,
          formatter: function (value: number) {
            return '{value|' + value.toFixed(1) + '}{unit|分}';
          },
          rich: {
            value: {
              fontSize: 32,
              fontWeight: 'bolder',
              color: score >= passingScore ? '#67C23A' : '#F56C6C' // Dynamic text color
            },
            unit: {
              fontSize: 18,
              color: '#999',
              padding: [0, 0, -10, 5]
            }
          }
        },
        data: [
          {
            value: score,
            name: title
          }
        ]
      }
    ]
  };
  
  gaugeChart.setOption(option);
}

// 监听窗口大小变化，调整图表大小
window.addEventListener('resize', () => {
  gaugeChart && gaugeChart.resize()
})

// 解析 requirements 并设置题型
const availableQuizTypes = ref<string[]>([])
const availableSpecificTypes = ref<Record<string, string[]>>({})
const selectedSpecificType = ref('')

// 扁平化的题型选项
const flatQuizOptions = computed(() => {
  const options: any[] = []
  
  // 遍历所有有具体题型的大类
  for (const category of availableQuizTypes.value) {
    const specificTypes = availableSpecificTypes.value[category] || []
    
    // 如果该大类有具体题型，则添加到选项中
    specificTypes.forEach(type => {
      // 避免重复（虽然理论上不会，但为了安全）
      if (!options.some(o => o.value === type && o.category === category)) {
        options.push({
          label: type, // 直接显示具体题型名称
          value: type,
          category: category,
          categoryLabel: getCategoryLabel(category) // 可选：显示所属大类，例如 "听写 (听力)"
        })
      }
    })
  }
  
  return options
})

const getCategoryLabel = (category: string) => {
  const map: Record<string, string> = {
    'listening': '听力',
    'reading': '阅读',
    'translation': '翻译',
    'writing': '写作',
    'vocabulary': '词汇'
  }
  return map[category] || category
}

// 简单的 Select 绑定值
const selectedFlatType = computed({
  get: () => {
    return selectedSpecificType.value
  },
  set: (val: string) => {
    selectedSpecificType.value = val
    // 反查所属大类并设置 quizForm.quiz_type
    const option = flatQuizOptions.value.find(o => o.value === val)
    if (option) {
      quizForm.quiz_type = option.category as any
    }
  }
})

// 解析出题要求
const parseRequirementsAndSetType = (req: string) => {
  availableQuizTypes.value = []
  availableSpecificTypes.value = {}
  selectedSpecificType.value = ''
  
  try {
    const data = JSON.parse(req)
    
    // 优先使用后端AI分类结果 (data.categorized)
    if (data.categorized) {
       for (const [category, types] of Object.entries(data.categorized)) {
          const typeList = Array.isArray(types) ? types : []
          availableSpecificTypes.value[category] = typeList
          if (typeList.length > 0) {
             availableQuizTypes.value.push(category)
          }
       }
    } else {
        // Fallback: 旧的关键词匹配逻辑
        // 检查是否有 type 或 types 字段
        let types: string[] = []
        
        if (data.type) {
          types = Array.isArray(data.type) ? data.type : [data.type]
        } else if (data.types) {
          types = Array.isArray(data.types) ? data.types : [data.types]
        }
        
        // 题型分类映射
        const categoryMap: Record<string, string[]> = {
          'listening': ['听力', 'listening', 'news', 'conversation', 'dictation', '听写', '对话', '新闻', '长对话', '短对话', 'long conversation', 'short conversation', 'report', '报道', 'speech', '讲话', 'lecture', '讲座', '听音', '听录音', '复述', '情景反应'],
          'reading': ['阅读', 'reading', 'passage', 'cloze', 'matching', 'fast reading', 'banked', 'skimming', 'scanning', '选词', '匹配', '仔细阅读', 'careful reading', '快速阅读', 'section a', 'section b', 'section c'],
          'translation': ['翻译', 'translation', 'sentence', 'paragraph', '句子', '段落', '中译英', '英译中', '汉译英', '英译汉', 'chinese to english', 'english to chinese', 'c-e', 'e-c', '译'],
          'writing': ['写作', 'writing', 'essay', 'composition', 'letter', 'email', '短文', '应用文', '通知', 'notice', 'memo', '备忘录', '改写'],
          'vocabulary': ['词汇', 'vocabulary', 'word', 'grammar', '语法', '单词', '短语', 'phrase', 'spelling', '拼写', '看中写英', '语境填空', '改错', '搭配', 'choice', '选择', '填空']
        }
        
        // 遍历提取的题型进行分类
        types.forEach(t => {
           let matched = false
           const lowerT = t.toLowerCase()
           
           for (const [mainCat, keywords] of Object.entries(categoryMap)) {
               if (keywords.some(k => lowerT.includes(k.toLowerCase()))) {
                   if (!availableQuizTypes.value.includes(mainCat)) {
                       availableQuizTypes.value.push(mainCat)
                   }
                   if (!availableSpecificTypes.value[mainCat]) {
                       availableSpecificTypes.value[mainCat] = []
                   }
                   // 避免重复
                   if (!availableSpecificTypes.value[mainCat].includes(t)) {
                       availableSpecificTypes.value[mainCat].push(t)
                   }
                   matched = true
                   break 
               }
           }
        })
    }
    
    // 如果没有找到有效分类，清空（UI会显示默认所有选项）
    // 如果找到了，自动选择第一个
    if (availableQuizTypes.value.length > 0) {
      // 自动选择第一个可用的具体题型
      const firstCategory = availableQuizTypes.value[0]
      const specificTypes = availableSpecificTypes.value[firstCategory]
      if (specificTypes && specificTypes.length > 0) {
         selectedFlatType.value = specificTypes[0]
      }
    }
  } catch (e) {
    console.error('Failed to parse requirements:', e)
    availableQuizTypes.value = []
  }
}

const updateListeningAnswer = (index: number, cn: string, en: string) => {
  // 将中文听写和英文回答合并为JSON字符串存储
  userAnswers.value[index] = JSON.stringify({
    cn: cn || '',
    en: en || ''
  })
}

const getListeningAnswer = (answerJson: string, key: 'cn' | 'en') => {
  try {
    if (!answerJson) return '未作答'
    const obj = JSON.parse(answerJson)
    return obj[key] || '未作答'
  } catch (e) {
    return answerJson // 如果解析失败，可能是旧数据或直接文本，原样返回
  }
}

onMounted(async () => {
  await chapterStore.fetchChapters()
  
  // Set default chapter for stats overview
  if (chapterStore.chapters.length > 0) {
    selectedStatsChapter.value = chapterStore.chapters[0].id
  }
  
  // if (chapterStore.chapters.length > 0) {
  //   quizForm.chapter_id = chapterStore.chapters[0].id
  // }

  // 初始获取全局统计
  if (quizForm.practice_mode !== 'random') {
    fetchOverallStats()
  }

  // 检查URL query参数，如果有mode参数则自动切换到对应模式
  const route = router.currentRoute.value
  if (route.query.mode) {
    const mode = route.query.mode as string
    if (['chapter', 'random', 'comprehensive'].includes(mode)) {
      quizForm.practice_mode = mode
    }
    // 清除query参数，保持URL简洁
    router.replace({ path: '/quiz' })
  }

  fetchHistory()

  // 检查是否从学情分析页面传递了quiz数据
  const routeState = history.state as any
  if (routeState && routeState.quizData) {
    // 直接初始化quiz
    initQuiz(routeState.quizData)
    ElMessage.success('已加载针对性练习')
    // 清除state，避免刷新页面时重复加载
    router.replace({ name: 'Quiz' })
  }
})

onUnmounted(() => {
  stopTimer()
})

const fetchHistory = async () => {
  try {
    const params: any = {
      practice_mode: quizForm.practice_mode,
      limit: 10
    }

    // 如果是章节练习，且已选择章节/小节，则添加过滤条件
    if (quizForm.practice_mode === 'chapter') {
      if (quizForm.chapter_id) {
        params.chapter_id = quizForm.chapter_id
      }
      if (quizForm.subsection_id) {
        params.subsection_id = quizForm.subsection_id
      }
    }

    // 根据当前选择的练习方式获取历史记录
    const res: any = await getQuizHistory(params)
    quizHistory.value = res || []
  } catch (e) {
    console.error(e)
  }
}

const handleCreateQuiz = async () => {
  if (quizForm.practice_mode === 'chapter' && !quizForm.subsection_id) {
    ElMessage.warning('请选择具体小节后再出题')
    return
  }
  if (quizForm.practice_mode === 'random' && !quizForm.section_id) {
    ElMessage.warning('请选择具体节(Section)后再出题')
    return
  }

  creating.value = true

  // 根据练习方式显示不同的加载文本
  if (quizForm.practice_mode === 'chapter') {
    loadingText.value = '正在生成题目...'
    if (quizForm.subsection_id) {
       loadingSubText.value = 'AI正在根据选定小节的出题要求精心准备题目'
    } else {
       loadingSubText.value = 'AI正在根据章节内容精心准备题目'
    }
  } else if (quizForm.practice_mode === 'random') {
    loadingText.value = '正在生成综合训练题目...'
    loadingSubText.value = 'AI正在根据本节内容进行综合出题'
  } else {
    loadingText.value = '正在分析薄弱点...'
    loadingSubText.value = 'AI正在分析你的学情，生成针对性题目'
  }

  loadingProgress.value = 0
  // 不要在这里清空，保留上一次的显示（如果有的话）
  // sourceDocumentsInfo.value = []

  try {
    let res: any

    // 🔥 综合练习：调用专门的综合练习接口
    if (quizForm.practice_mode === 'comprehensive') {
      // 1. Ensure we have weak points data
      if (weakPointsData.value.length === 0) {
        loadingText.value = '正在获取学情数据...'
        await fetchWeakPointsData()
      }

      if (weakPointsData.value.length === 0) {
        ElMessage.warning('暂无薄弱点数据，请先完成一些章节练习')
        creating.value = false
        return
      }

      // 2. Randomly select one weak point
      const randomIndex = Math.floor(Math.random() * weakPointsData.value.length)
      const selectedWP = weakPointsData.value[randomIndex]
      console.log('Selected Weak Point for Training:', selectedWP)

      // 3. Find corresponding subsection_id
      let targetSubsectionId: number | undefined = undefined
      
      // Helper to find subsection
      // We iterate through the chapter store to find a subsection that matches the weak point title
      const findSubsection = (wpTitle: string) => {
         if (!chapterStore.chapters) return undefined
         
         for (const chapter of chapterStore.chapters) {
            if (chapter.sections) {
               for (const section of chapter.sections) {
                  if (section.subsections) {
                     for (const sub of section.subsections) {
                        // Check if wpTitle contains sub.title
                        // wpTitle format is typically "第X章 - X.X.X Title"
                        // sub.title is typically "X.X.X Title"
                        if (wpTitle.includes(sub.title)) {
                           return sub.id
                        }
                     }
                  }
               }
            }
         }
         return undefined
      }

      targetSubsectionId = findSubsection(selectedWP.knowledge_point_id)

      if (!targetSubsectionId) {
         console.warn('Could not find subsection for weak point:', selectedWP.knowledge_point_id)
         // Fallback: try to just pick a random subsection if strict matching fails? 
         // Or just show error. User said "Randomly select... contents...". 
         // If we can't find content, we can't generate.
         ElMessage.warning(`无法找到薄弱点 "${selectedWP.knowledge_point_id}" 对应的练习内容，请尝试其他模式`)
         creating.value = false
         return
      }

      // 4. Call generation API (Using the same logic as Chapter Training - generateWordTraining)
      // This ensures we use the subsection's content and AI prompts
      loadingText.value = '正在生成针对性训练...'
      loadingSubText.value = `AI正在根据薄弱点 "${selectedWP.knowledge_point_id}" 准备题目`
      
      res = await generateWordTraining({
         subsection_id: targetSubsectionId,
         count: quizForm.question_count,
         practice_mode: 'comprehensive'
      })

    } else if (quizForm.practice_mode === 'random') {
       // Comprehensive Training (Section based) Logic
       res = await createSectionComprehensiveQuiz({
         section_id: quizForm.section_id!,
         difficulty: quizForm.difficulty,
         count: quizForm.question_count
       })
    } else {
      // 章节练习和随机练习
      if (quizForm.practice_mode === 'chapter' && quizForm.subsection_id) {
          // Word Training Logic (Default for Chapter Training with Subsection)
          loadingText.value = '正在生成单词训练...'
          loadingSubText.value = '正在智能筛选高频错词与生词...'
          res = await generateWordTraining({
             subsection_id: quizForm.subsection_id,
             count: quizForm.question_count
          })
      } else {
          // 调用原有接口 (Random / Comprehensive)
          const submitData = { ...quizForm }
          if (quizForm.practice_mode !== 'chapter' && selectedSpecificType.value) {
              submitData.quiz_type = `${quizForm.quiz_type}:${selectedSpecificType.value}` as any
          }
          res = await createQuiz(submitData)
      }
    }

    // 显示使用的文档信息 - 立即显示
    if (res.source_documents && res.source_documents.length > 0) {
      sourceDocumentsInfo.value = res.source_documents
      sourceChunksInfo.value = res.source_chunks || []
      ragContextPreview.value = res.rag_context || ''
      rulesPreview.value = res.applied_rules || ''
      loadingText.value = '题目生成成功！'
      loadingSubText.value = `已根据 ${res.source_documents.length} 个文档生成题目`
      console.log('出题使用的文档:', res.source_documents)
    } else {
      console.warn('未返回source_documents信息')
      loadingText.value = '题目生成成功！'
      loadingSubText.value = 'AI已为你准备好题目'
    }

    // 延迟一下让用户看到文档信息
    await new Promise(resolve => setTimeout(resolve, 2000))

    // 综合练习返回的格式是 { success, quiz, ... }，需要提取quiz对象
    const quizData = res.quiz || res
    initQuiz(quizData)

    ElNotification({
      title: '✅ 出题成功',
      message: `已为你生成 ${quizData.question_count || res.question_count} 道${quizForm.practice_mode === 'comprehensive' ? '推荐' : (quizForm.practice_mode === 'random' ? '综合' : getQuizTypeLabel(quizData.quiz_type))}题目，加油答题吧！`,
      type: 'success',
      duration: 3000
    })
  } catch (error: any) {
    ElNotification({
      title: '❌ 出题失败',
      message: error.message || '创建练习失败，请稍后重试',
      type: 'error',
      duration: 3000
    })
  } finally {
    creating.value = false
    loadingProgress.value = 100
    // 不要在这里清空sourceDocumentsInfo，让用户看完文档信息
    // 下次生成题目时会自动更新
  }
}

const handlePersonalizedQuiz = async () => {
  if (!quizForm.chapter_id) {
    ElMessage.warning('请选择章节')
    return
  }
  creating.value = true
  loadingText.value = '智能推荐中...'
  loadingSubText.value = 'AI正在分析你的学习情况，推荐针对性题目'
  loadingProgress.value = 0
  // 不要在这里清空，保留上一次的显示
  // sourceDocumentsInfo.value = []

  try {
    const res: any = await createPersonalizedQuiz(quizForm)

    // 显示使用的文档信息 - 立即显示
    if (res.source_documents && res.source_documents.length > 0) {
      sourceDocumentsInfo.value = res.source_documents
      sourceChunksInfo.value = res.source_chunks || []
      ragContextPreview.value = res.rag_context || ''
      loadingText.value = '智能推荐完成！'
      loadingSubText.value = `已根据 ${res.source_documents.length} 个文档推荐针对性题目`
      console.log('智能推荐使用的文档:', res.source_documents)
    } else {
      console.warn('未返回source_documents信息')
      loadingText.value = '智能推荐完成！'
      loadingSubText.value = '已为你推荐针对性题目'
    }

    // 延迟一下让用户看到文档信息
    await new Promise(resolve => setTimeout(resolve, 2000))

    initQuiz(res)

    ElNotification({
      title: '🎯 智能推荐成功',
      message: `已根据你的薄弱点推荐 ${res.question_count} 道针对性题目！`,
      type: 'success',
      duration: 3000
    })
  } catch (error: any) {
    ElNotification({
      title: '❌ 推荐失败',
      message: error.message || '创建个性化练习失败，请稍后重试',
      type: 'error',
      duration: 3000
    })
  } finally {
    creating.value = false
    loadingProgress.value = 100
    // 不要在这里清空sourceDocumentsInfo
  }
}

const initQuiz = (quiz: any) => {
  console.log('=== initQuiz called ===')
  console.log('Quiz data:', quiz)
  console.log('quiz.practice_mode:', quiz.practice_mode)
  console.log('quiz.quiz_type:', quiz.quiz_type)
  console.log('quiz.questions:', quiz.questions)

  currentQuiz.value = quiz
  // questions 已经是数组了，不需要再次 JSON.parse
  questions.value = Array.isArray(quiz.questions) ? quiz.questions : JSON.parse(quiz.questions || '[]')

  console.log('Parsed questions count:', questions.value.length)
  if (questions.value.length > 0) {
    console.log('First question:', questions.value[0])
    console.log('First question quiz_type:', questions.value[0].quiz_type)
  }

  // 初始化答案数组
  userAnswers.value = questions.value.map(q => {
    const type = getQuestionType(q, quiz.quiz_type)
    if (type === 'listening') {
       // 如果选项是数组 -> 多选 -> 初始化 []
       if (Array.isArray(q.options)) {
         return []
       }
       // 否则单选 -> 初始化 ''
       return ''
    }
    return ''
  })

  timeSpent.value = 0
  startTimer()
}

const handleSubmit = async () => {
  // 准备答案数据
  const answers = userAnswers.value

  // 检查是否所有题目都已作答
  const hasEmpty = answers.some((ans) => {
    if (Array.isArray(ans)) return ans.length === 0
    return !ans || (typeof ans === 'string' && ans.trim() === '')
  })

  if (hasEmpty) {
    ElMessage.warning('请完成所有题目后再提交')
    return
  }

  submitting.value = true
  ElMessage.info({
    message: '正在提交答案，请稍候...',
    duration: 0,
    showClose: false
  })

  try {
    const res: any = await submitQuiz({
      quiz_id: currentQuiz.value.id,
      user_answers: answers,
      time_spent: timeSpent.value
    })
    result.value = res
    showResult.value = true
    stopTimer()
    fetchHistory()
    
    // 更新统计数据
    if (quizForm.practice_mode === 'comprehensive') {
        fetchWeakPointsData()
    } else if (quizForm.practice_mode === 'chapter' && quizForm.subsection_id) {
        // 如果是章节练习且选择了小节，更新小节统计
        fetchSubsectionStatsData(quizForm.subsection_id)
    } else {
        // 否则更新总体统计
        fetchOverallStats()
    }

    ElMessage.closeAll()

    ElNotification({
      title: res.accuracy >= 60 ? '🎉 完成练习' : '💪 继续加油',
      message: `得分: ${res.score.toFixed(1)}分 | 正确率: ${res.accuracy.toFixed(1)}%`,
      type: res.accuracy >= 60 ? 'success' : 'warning',
      duration: 3000
    })

    if (res.wrong_count > 0) {
      ElNotification({
        title: '📝 错题提示',
        message: `已自动记录 ${res.wrong_count} 道错题到错题库`,
        type: 'info',
        duration: 3000,
        offset: 70
      })
    }
  } catch (error: any) {
    ElMessage.closeAll()
    ElNotification({
      title: '❌ 提交失败',
      message: error.message || '提交失败，请稍后重试',
      type: 'error',
      duration: 3000
    })
  } finally {
    submitting.value = false
  }
}

const handleCancel = () => {
  stopTimer()
  currentQuiz.value = null
  questions.value = []
  userAnswers.value = []
}

const handleRetry = () => {
  showResult.value = false
  showDetailedResults.value = false
  currentQuiz.value = null
  questions.value = []
  userAnswers.value = []
  
  // 更新统计数据 (点击“返回”或“再做一次”时触发)
  if (quizForm.practice_mode === 'chapter' && quizForm.subsection_id) {
      // 如果是章节练习且选择了小节，更新小节统计
      fetchSubsectionStatsData(quizForm.subsection_id)
  } else {
      // 否则更新总体统计
      fetchOverallStats()
  }
}

const startTimer = () => {
  timer = setInterval(() => {
    timeSpent.value++
  }, 1000)
}

const stopTimer = () => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

const getQuizTypeLabel = (type: string) => {
  const labels: any = {
    listening: '听力理解',
    reading: '阅读理解',
    translation: '翻译练习',
    writing: '写作练习',
    comprehensive: '推荐训练',
    mixed: '综合训练',
    word_training: '单词训练',
    grammar: '语法训练'
  }
  return labels[type] || type
}

const getQuizTypeTagType = (type: string) => {
  const types: any = {
    listening: 'primary',
    reading: 'success',
    translation: 'warning',
    writing: 'danger',
    comprehensive: 'info',
    mixed: 'info',
    word_training: 'primary',
    grammar: 'warning'
  }
  return types[type] || ''
}

const getPracticeModeLabel = (mode: string) => {
  const labels: any = {
    chapter: '章节练习',
    random: '综合训练',
    comprehensive: '推荐训练'
  }
  return labels[mode] || mode
}

const getPracticeModeTagType = (mode: string) => {
  const types: any = {
    chapter: 'primary',
    random: 'success',
    comprehensive: 'warning'
  }
  return types[mode] || ''
}

// 监听练习方式变化，自动更新历史记录
watch(() => quizForm.practice_mode, (newMode) => {
  fetchHistory()
  
  // 切换模式时清空级联选择器
  selectedCascaderValue.value = []
  quizForm.chapter_id = 0
  quizForm.section_id = undefined
  quizForm.subsection_id = undefined
  subsectionStats.value = null
  
  // 综合训练不显示统计
  if (newMode === 'random') {
    overallStats.value = null
  } else if (newMode === 'chapter') {
    fetchOverallStats()
  } else if (newMode === 'comprehensive') {
    fetchWeakPointsData()
  }
})

// 监听章节和小节变化，自动更新历史记录
watch(() => [quizForm.chapter_id, quizForm.subsection_id], () => {
  if (quizForm.practice_mode === 'chapter') {
    fetchHistory()
  }
})

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const formatAnswer = (answer: any) => {
  if (typeof answer === 'object') {
    return JSON.stringify(answer, null, 2)
  }
  return answer
}

const hasOptions = (q: any) => {
  if (!q || !q.options) return false
  if (Array.isArray(q.options)) return q.options.length > 0
  if (typeof q.options === 'object') return Object.keys(q.options).length > 0
  return false
}

// 获取题目的实际类型（综合练习时使用题目自身的quiz_type）
const getQuestionType = (question: any, quizType: string) => {
  let type = quizType.split(':')[0]
  
  // 优先检查 question.quiz_type
  if (question && question.quiz_type) {
    type = question.quiz_type.split(':')[0]
  }
  // 其次检查 question.question_type (兼容性)
  else if (question && question.question_type) {
    type = question.question_type.split(':')[0]
  }
  
  // 规范化类型名称
  if (['fill_in_the_blank', 'dictation', 'spelling'].includes(type)) {
    return 'blank'
  }
  
  // 特殊处理：如果是听力类型但没有选项，且有正确答案，视为听写（blank）
  if (type === 'listening' && question) {
    if (!hasOptions(question) && question.correct_answer) {
      return 'blank';
    }
  }

  return type
}

const getOptionLabel = (key: string | number) => {
  // If key is a number (index), convert to Letter (0->A, 1->B, etc.)
  if (typeof key === 'number' || !isNaN(Number(key))) {
    const index = Number(key);
    // 0-25 -> A-Z
    if (index >= 0 && index < 26) {
      return String.fromCharCode(65 + index);
    }
  }
  return key;
}

const handleViewRecommendedDetail = async (quizId: number) => {
  try {
    const res: any = await getQuiz(quizId)
    recommendedHistoryDetail.value = res

    // 解析题目
    recommendedHistoryQuestions.value = Array.isArray(res.questions)
      ? res.questions
      : JSON.parse(res.questions || '[]')

    // 解析用户答案
    if (res.user_answers) {
      recommendedHistoryUserAnswers.value = Array.isArray(res.user_answers)
        ? res.user_answers
        : JSON.parse(res.user_answers || '[]')
    } else {
      recommendedHistoryUserAnswers.value = []
    }

    // 解析正确答案
    if (res.correct_answers) {
      recommendedHistoryCorrectAnswers.value = Array.isArray(res.correct_answers)
        ? res.correct_answers
        : JSON.parse(res.correct_answers || '[]')
    } else {
      recommendedHistoryCorrectAnswers.value = []
    }

    // 解析详细结果
    if (res.results) {
      recommendedHistoryResults.value = Array.isArray(res.results)
        ? res.results
        : JSON.parse(res.results || '[]')
    } else {
      recommendedHistoryResults.value = []
    }

    showRecommendedHistoryDetail.value = true
  } catch (error: any) {
    ElMessage.error(error.message || '获取练习详情失败')
  }
}

const handleViewDetail = async (quizId: number) => {
  try {
    const res: any = await getQuiz(quizId)
    historyDetail.value = res

    // 解析题目
    historyQuestions.value = Array.isArray(res.questions)
      ? res.questions
      : JSON.parse(res.questions || '[]')

    // 解析用户答案
    if (res.user_answers) {
      historyUserAnswers.value = Array.isArray(res.user_answers)
        ? res.user_answers
        : JSON.parse(res.user_answers || '[]')
    } else {
      historyUserAnswers.value = []
    }

    // 解析正确答案
    if (res.correct_answers) {
      historyCorrectAnswers.value = Array.isArray(res.correct_answers)
        ? res.correct_answers
        : JSON.parse(res.correct_answers || '[]')
    } else {
      historyCorrectAnswers.value = []
    }

    // 解析详细结果
    if (res.results) {
      historyResults.value = Array.isArray(res.results)
        ? res.results
        : JSON.parse(res.results || '[]')
    } else {
      historyResults.value = []
    }

    showHistoryDetail.value = true
  } catch (error: any) {
    ElMessage.error(error.message || '获取练习详情失败')
  }
}

const isHistoryAnswerCorrect = (index: number) => {
  if (!historyDetail.value.is_completed) return false

  const userAnswer = historyUserAnswers.value[index]
  const correctAnswer = historyCorrectAnswers.value[index]
  const question = historyQuestions.value[index]

  // 获取题目的实际类型
  const questionType = getQuestionType(question, historyDetail.value.quiz_type)

  if (questionType === 'listening') {
     // 听力题：数组比较（忽略顺序）
     if (Array.isArray(userAnswer) && Array.isArray(correctAnswer)) {
         if (userAnswer.length !== correctAnswer.length) return false
         const sortedUser = [...userAnswer].sort()
         const sortedCorrect = [...correctAnswer].sort()
         return sortedUser.every((val, i) => val === sortedCorrect[i])
     }
     // 单选模式：直接比较
     return String(userAnswer).toUpperCase() === String(correctAnswer).toUpperCase()
  }

  if (questionType === 'reading' || questionType === 'vocabulary') {
    // 选择题：直接比较
    return String(userAnswer).toUpperCase() === String(correctAnswer).toUpperCase()
  }

  // 对于翻译和写作，基于分数判断
  if (questionType === 'translation' || questionType === 'writing') {
    // 从 historyResults 中获取该题的分数
    if (historyResults.value && historyResults.value[index]) {
      const result = historyResults.value[index]
      // score 是 0-1 的浮点数，转换为百分制
      const scorePercent = result.score * 100
      // 60分及以上算正确
      return scorePercent >= 60
    }
    // 如果没有结果数据，fallback 到 is_correct 字段
    if (historyResults.value && historyResults.value[index]) {
      return historyResults.value[index].is_correct
    }
  }

  // 其他情况：简单比较字符串
  return JSON.stringify(userAnswer) === JSON.stringify(correctAnswer)
}

const isRecommendedHistoryAnswerCorrect = (index: number) => {
  if (!recommendedHistoryDetail.value.is_completed) return false

  const userAnswer = recommendedHistoryUserAnswers.value[index]
  const correctAnswer = recommendedHistoryCorrectAnswers.value[index]
  const question = recommendedHistoryQuestions.value[index]

  // 获取题目的实际类型
  const questionType = getQuestionType(question, recommendedHistoryDetail.value.quiz_type)

  if (questionType === 'listening') {
     // 听力题：数组比较（忽略顺序）
     if (Array.isArray(userAnswer) && Array.isArray(correctAnswer)) {
         if (userAnswer.length !== correctAnswer.length) return false
         const sortedUser = [...userAnswer].sort()
         const sortedCorrect = [...correctAnswer].sort()
         return sortedUser.every((val, i) => val === sortedCorrect[i])
     }
     // 单选模式：直接比较
     return String(userAnswer).toUpperCase() === String(correctAnswer).toUpperCase()
  }

  if (questionType === 'reading' || questionType === 'vocabulary') {
    // 选择题：直接比较
    return String(userAnswer).toUpperCase() === String(correctAnswer).toUpperCase()
  }

  // 对于翻译和写作，基于分数判断
  if (questionType === 'translation' || questionType === 'writing') {
    // 从 recommendedHistoryResults 中获取该题的分数
    if (recommendedHistoryResults.value && recommendedHistoryResults.value[index]) {
      const result = recommendedHistoryResults.value[index]
      // score 是 0-1 的浮点数，转换为百分制
      const scorePercent = result.score * 100
      // 60分及以上算正确
      return scorePercent >= 60
    }
    // 如果没有结果数据，fallback 到 is_correct 字段
    if (recommendedHistoryResults.value && recommendedHistoryResults.value[index]) {
      return recommendedHistoryResults.value[index].is_correct
    }
  }

  // 其他情况：简单比较字符串
  return JSON.stringify(userAnswer) === JSON.stringify(correctAnswer)
}

const getDocTypeLabel = (docType: string) => {
  const labels: any = {
    'textbook': '教材',
    'teaching_plan': '教案',
    'exercise': '练习',
    'knowledge': '知识点文档'
  }
  return labels[docType] || '文档'
}

const getDocTypeTag = (docType: string) => {
  const tags: any = {
    'textbook': 'primary',
    'teaching_plan': 'success',
    'exercise': 'warning',
    'knowledge': 'primary'
  }
  return tags[docType] || 'info'
}

const getAudioUrl = (audioUrl: string) => {
  // 如果是完整的URL，直接返回
  if (audioUrl.startsWith('http://') || audioUrl.startsWith('https://')) {
    return audioUrl
  }
  // 否则，拼接后端API的baseURL
  // 假设后端运行在 http://localhost:8000
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  return `${baseURL}${audioUrl}`
}

// 获取综合练习中的所有题型
const getQuestionTypes = (quizRecord: any) => {
  if (!quizRecord || !quizRecord.questions) {
    return []
  }

  try {
    // 解析questions（可能是字符串或已经是数组）
    const questions = typeof quizRecord.questions === 'string'
      ? JSON.parse(quizRecord.questions)
      : quizRecord.questions

    if (!Array.isArray(questions)) {
      return []
    }

    // 提取所有题型并去重
    const types = new Set<string>()
    questions.forEach((q: any) => {
      if (q.quiz_type) {
        types.add(q.quiz_type)
      }
    })

    // 如果没有找到question级别的quiz_type，使用record级别的
    if (types.size === 0 && quizRecord.quiz_type) {
      types.add(quizRecord.quiz_type)
    }

    return Array.from(types)
  } catch (e) {
    console.error('Error parsing question types:', e)
    // 出错时返回record级别的quiz_type
    return quizRecord.quiz_type ? [quizRecord.quiz_type] : []
  }
}

</script>

<style scoped>
.quiz-container {
  padding: 20px;
  position: relative;
}

/* Quiz Header */
.quiz-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
}

.quiz-title {
  font-size: 24px;
  font-weight: bold;
  min-width: 100px;
}

.mode-switch {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.large-radio {
  margin: 0 15px !important;
}

.large-radio :deep(.el-radio-button__inner) {
  border: 1px solid #dcdfe6 !important;
  border-radius: 4px !important;
  box-shadow: none !important;
  padding: 12px 25px;
  font-size: 16px;
}

.large-radio :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background-color: #409EFF;
  border-color: #409EFF !important;
  color: white;
  box-shadow: none !important;
}

/* Section Title */
.section-title {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 20px;
  color: #303133;
}

/* Stats Card Styles */
.stats-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  height: 100%; /* Fill column height */
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.sticky-card {
  position: sticky;
  top: 20px;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title-group {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-icon {
  margin-right: 8px;
  color: #409EFF;
  font-size: 18px;
}

.stats-title-text {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.stats-subtitle-tag {
  font-size: 14px !important;
  padding: 16px 12px !important;
  font-weight: 500;
}

.stats-content {
  padding: 10px 5px;
}

/* Overview Section */
.stats-overview {
  display: flex;
  justify-content: space-around;
  align-items: center;
  margin-bottom: 20px;
}

.overview-item {
  text-align: center;
}

.overview-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.overview-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.overview-divider {
  width: 1px;
  height: 30px;
  background-color: #E4E7ED;
}

/* Chart Section */
.chart-wrapper {
  height: 300px;
  width: 100%;
  display: flex;
  justify-content: center;
  margin-bottom: 10px;
}

.gauge-chart {
  width: 100%;
  height: 100%;
}

/* Final Score Card */
.final-score-card {
  background: linear-gradient(135deg, #f5f7fa 0%, #eef1f6 100%);
  border-radius: 12px;
  padding: 20px 10px;
  border: 1px solid #e4e7ed;
  margin-top: 15px;
}

.score-row {
  display: flex;
  justify-content: space-around;
  align-items: center;
}

.score-col {
  text-align: center;
  flex: 1;
}

.score-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.weight-tag {
  font-size: 12px;
  color: #909399;
  background-color: #fff;
  padding: 2px 6px;
  border-radius: 10px;
  border: 1px solid #dcdfe6;
}

.score-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.score-value.highlight {
  color: #67C23A;
  text-shadow: 0 2px 4px rgba(103, 194, 58, 0.2);
}

.score-value.pass-val {
  font-size: 36px;
  color: #E6A23C;
}

.score-sub {
  font-size: 14px;
  color: #909399;
  font-weight: normal;
  margin-left: 2px;
}

.score-divider-vertical {
  width: 1px;
  height: 40px;
  background-color: #DCDFE6;
}

/* 加载弹窗样式 */
:deep(.loading-dialog) {
  border-radius: 12px;
}

:deep(.loading-dialog .el-dialog__header) {
  display: none;
}

:deep(.loading-dialog .el-dialog__body) {
  padding: 0;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 60px;
}

.loading-icon {
  margin-bottom: 20px;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.loading-content h3 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 20px;
  font-weight: 600;
}

.loading-content p {
  margin: 0 0 20px 0;
  color: #909399;
  font-size: 14px;
}

.loading-content .el-progress {
  width: 100%;
}

.quiz-form {
  margin-bottom: 20px;
}

.quiz-card {
  margin-top: 20px;
}

.question-item {
  margin-bottom: 40px;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
}

.question-title {
  margin-bottom: 15px;
  font-size: 16px;
  color: #303133;
}

.question-number {
  display: inline-block;
  min-width: 30px;
  font-weight: bold;
  color: #409EFF;
}

.answer-group {
  display: flex;
  flex-direction: column;
}

/* 横向选项布局 */
.horizontal-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 确保所有 radio 选项的对齐一致 */
:deep(.horizontal-options .el-radio) {
  margin-right: 0;
  height: auto;
}

.answer-option {
  margin-bottom: 10px;
  padding: 10px;
  background: white;
  border-radius: 4px;
}

.horizontal-option {
  width: 100%;
  margin-bottom: 0;
  margin-right: 0;
  margin-left: 0;
  padding: 12px 15px;
  border: 1.5px solid #DCDFE6;
  transition: all 0.3s;
  display: flex;
  align-items: center;  /* 垂直居中对齐 */
}

/* 重置 Element Plus radio 的默认样式 */
:deep(.horizontal-option .el-radio__label) {
  padding-left: 0;
  display: flex;
  align-items: center;
  width: 100%;
}

:deep(.horizontal-option .el-radio__inner) {
  margin-right: 8px;
}

.horizontal-option:hover {
  border-color: #409EFF;
  background: #f0f9ff;
}

.horizontal-option .option-key {
  display: inline-block;
  min-width: 28px;
  font-weight: 600;
  color: #409EFF;
  font-size: 15px;
  flex-shrink: 0;
  line-height: 1.6;
}

.horizontal-option .option-text {
  margin-left: 8px;
  line-height: 1.6;
  color: #303133;
  flex: 1;
}

.matching-question {
  background: white;
  padding: 15px;
  border-radius: 4px;
}

.matching-item {
  padding: 10px;
  margin-bottom: 10px;
  background: #f0f2f5;
  border-radius: 4px;
}

.ordering-question {
  background: white;
  padding: 15px;
  border-radius: 4px;
}

.hint-text {
  color: #909399;
  margin-bottom: 10px;
}

.draggable-list {
  min-height: 100px;
}

.draggable-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  background: #f0f2f5;
  border-radius: 4px;
  cursor: move;
  transition: all 0.3s;
}

.draggable-item:hover {
  background: #e4e7ed;
  transform: translateX(5px);
}

.drag-handle {
  margin-right: 10px;
  color: #909399;
}

/* Custom style for chapter selector in stats card */
.chapter-select :deep(.el-input__inner) {
  font-size: 18px !important;
  font-weight: 500;
  color: #303133;
}

.chapter-select :deep(.el-input__wrapper) {
  padding: 4px 12px;
}

.result-stats {
  display: flex;
  justify-content: space-around;
  margin: 20px 0;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  color: #909399;
  font-size: 14px;
  margin-bottom: 5px;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}

.stat-value.error {
  color: #F56C6C;
}

.result-item {
  margin-bottom: 25px;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 8px;
}

.result-item h4 {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.score-badge {
  font-size: 14px;
  color: #409EFF;
  margin-left: 10px;
}

.result-content {
  padding: 10px;
  background: white;
  border-radius: 4px;
}

.result-content p {
  margin: 8px 0;
  line-height: 1.6;
}

.feedback {
  color: #409EFF;
  background: #ecf5ff;
  padding: 10px;
  border-radius: 4px;
  border-left: 3px solid #409EFF;
}

.explanation {
  color: #67C23A;
  background: #f0f9ff;
  padding: 10px;
  border-radius: 4px;
  border-left: 3px solid #67C23A;
}

/* 音频文本解析样式 */
.audio-text-explanation {
  margin-top: 15px;
  padding: 12px;
  background: #fff9e6;
  border-radius: 8px;
  border-left: 4px solid #E6A23C;
}

.audio-text-explanation strong {
  color: #E6A23C;
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
}

.audio-text-content {
  margin: 0;
  padding: 10px;
  background: white;
  border-radius: 4px;
  font-family: inherit;
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.8;
  color: #606266;
  border: 1px solid #f0e6d2;
}

/* Meta Info Styles */
.meta-info-box {
  margin: 15px 0;
  border-radius: 4px;
}

.meta-descriptions :deep(.el-collapse-item__header) {
  font-size: 13px;
  color: #909399;
  height: 36px;
  line-height: 36px;
  border-bottom: none;
}

.meta-descriptions :deep(.el-collapse-item__content) {
  padding-bottom: 10px;
}

.knowledge-content, .prompt-content {
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  line-height: 1.6;
  color: #606266;
  font-size: 14px;
  max-height: 200px;
  overflow-y: auto;
}

.sample-essay {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  border-left: 4px solid #409EFF;
  white-space: pre-wrap;
  line-height: 1.6;
  color: #303133;
  font-size: 15px;
  margin-top: 10px;
}

/* 历史详情样式 */
.not-completed-hint {
  margin-bottom: 20px;
}

.history-question-item {
  margin-bottom: 30px;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
}

.answer-display {
  padding: 15px;
  background: white;
  border-radius: 4px;
  margin-top: 10px;
}

.option-item {
  padding: 10px;
  margin-bottom: 8px;
  border-radius: 4px;
  background: #f5f7fa;
}

.option-label {
  display: flex;
  align-items: center;
}

.option-key-history {
  display: inline-block;
  min-width: 28px;
  font-weight: 600;
  color: #409EFF;
  flex-shrink: 0;
}

.option-text-history {
  margin-left: 8px;
  line-height: 1.6;
  flex: 1;
}

.correct-option {
  background: #f0f9ff !important;
  border-left: 3px solid #67C23A;
  color: #67C23A;
  font-weight: bold;
}

.correct-option .option-key-history {
  color: #67C23A;
}

.error-text {
  color: #F56C6C !important;
}

.success-text {
  color: #67C23A !important;
}

.min-req {
  font-size: 14px;
  color: #909399;
  margin-left: 2px;
  font-weight: normal;
}

.user-option {
  background: #e6f7ff !important;
  border-left: 3px solid #409EFF;
}

.wrong-option {
  background: #fef0f0 !important;
  border-left: 3px solid #F56C6C;
  color: #F56C6C;
}

.wrong-option .option-key-history {
  color: #F56C6C;
}

/* Meta信息样式 */
.meta-info-box {
  margin: 10px 0 15px 0;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.meta-descriptions :deep(.el-descriptions__label) {
  width: 100px;
  background-color: #f0f2f5;
  color: #606266;
  font-weight: 500;
}

.prompt-content {
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 12px;
  color: #606266;
  background-color: #fafafa;
  padding: 10px;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
}

.knowledge-content {
  font-size: 13px;
  color: #303133;
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.6;
  background: #ecf5ff;
  padding: 8px 12px;
  border-radius: 4px;
  border-left: 3px solid #409EFF;
  max-height: 200px;
  overflow-y: auto;
}

.explanation-box {
  margin-top: 15px;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 4px;
  border-left: 3px solid #67C23A;
  color: #67C23A;
}

/* 新题型样式 */
.listening-question,
.reading-question,
.translation-question,
.writing-question {
  margin-top: 15px;
}

.audio-text-box,
.passage-box {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 15px;
}

.audio-text-box h5,
.passage-box h5 {
  margin: 0 0 10px 0;
  color: #409EFF;
  font-weight: bold;
}

/* 音频播放器样式 */
.audio-player-box {
  padding: 15px;
  background: #f0f9ff;
  border-radius: 8px;
  margin-bottom: 15px;
  border-left: 4px solid #409EFF;
}

.audio-player-box h5 {
  margin: 0 0 12px 0;
  color: #409EFF;
  font-weight: bold;
  font-size: 15px;
}

.audio-player {
  width: 100%;
  max-width: 600px;
  outline: none;
}

.audio-player::-webkit-media-controls-panel {
  background-color: #fff;
  border-radius: 4px;
}

.audio-text-box p,
.passage-box p {
  line-height: 1.8;
  color: #606266;
  margin: 0;
}

.key-points-box {
  padding: 12px;
  background: #fff3e0;
  border-radius: 4px;
  border-left: 3px solid #E6A23C;
  margin-bottom: 15px;
}

.key-points-box h5 {
  margin: 0 0 8px 0;
  color: #E6A23C;
  font-weight: bold;
}

.key-points-box ul {
  margin: 0;
  padding-left: 20px;
}

.key-points-box li {
  color: #606266;
  line-height: 1.6;
  margin-bottom: 5px;
}

.writing-requirements {
  padding: 15px;
  background: #f0f9ff;
  border-radius: 4px;
  border-left: 3px solid #409EFF;
  margin-bottom: 15px;
}

.writing-requirements h5 {
  margin: 0 0 10px 0;
  color: #409EFF;
  font-weight: bold;
}

.writing-requirements ul {
  margin: 10px 0;
  padding-left: 20px;
}

.writing-requirements li {
  color: #606266;
  line-height: 1.6;
  margin-bottom: 5px;
}

.writing-requirements p {
  margin: 8px 0;
  color: #606266;
}

.user-writing {
  padding: 15px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin-top: 10px;
}

/* 写作题参考范文样式 */
.sample-essay {
  padding: 15px;
  background: #f0f9ff;
  border: 1px solid #d9ecff;
  border-radius: 8px;
  border-left: 4px solid #409EFF;
  line-height: 1.8;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #606266;
  margin: 10px 0;
  font-family: 'Georgia', serif;
}

/* 详细反馈样式 */
.feedback,
.feedback-box {
  margin: 15px 0;
  padding: 15px;
  background: #fff7e6;
  border: 1px solid #ffd666;
  border-radius: 8px;
  border-left: 4px solid #faad14;
}

.feedback-content,
.feedback-text {
  margin: 10px 0 0 0;
  padding: 0;
  font-family: inherit;
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 2;
  color: #262626;
  background: none;
  border: none;
  font-size: 14px;
}

/* Chapter Overview New Styles */
.chapter-total-score {
  text-align: center;
  padding: 20px 0;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 15px;
}

.chapter-total-score.passed .score-num {
  color: #67C23A;
}

.score-circle {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.score-num {
  font-size: 48px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.score-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.score-target {
  margin-top: 10px;
  font-size: 14px;
  color: #606266;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.subsection-stats-list {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 5px;
}

.sub-stat-item {
  margin-bottom: 15px;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.sub-stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.sub-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 70%;
}

.sub-stat-body {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
}

.stat-row {
  display: flex;
  align-items: center;
  gap: 5px;
}

.stat-row .label {
  color: #909399;
}

.stat-row .value {
  font-weight: 500;
}

.stat-row .score-val {
  font-weight: bold;
  color: #409EFF;
}

.status-tip {
  color: #F56C6C;
  font-size: 12px;
  margin-left: 2px;
}

/* 反馈中的特殊标记样式 */
.feedback-content strong,
.feedback-text strong {
  color: #1890ff;
  font-weight: 600;
}

/* 句子改进建议的特殊样式 */
.feedback-content:deep(【句子),
.feedback-text:deep(【句子) {
  display: block;
  margin-top: 15px;
  padding: 8px 12px;
  background: #e6f7ff;
  border-radius: 4px;
  font-weight: bold;
  color: #0050b3;
}

/* 文档信息显示 */
.source-documents-info {
  width: 100%;
  margin-top: 15px;
  padding: 10px;
  background: #f0f9ff;
  border-radius: 8px;
  border-left: 3px solid #409EFF;
}

.doc-item {
  margin: 5px 0;
  padding: 5px 8px;
  background: white;
  border-radius: 4px;
  display: flex;
  align-items: center;
}

/* Weak Points Overview Styles */
.weak-points-overview .stats-content {
  padding: 0;
}

.weak-points-list {
  max-height: 500px;
  overflow-y: auto;
}

.wp-header {
  display: flex;
  align-items: center;
  width: 100%;
  padding-right: 10px;
}

.wp-title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 65%;
  margin-right: 10px;
}

.wp-details {
  padding: 10px;
  background-color: #f8f9fa;
}

.wp-stat-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 13px;
  color: #606266;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 8px;
}

.detail-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  background-color: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 8px;
}

.detail-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.detail-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 75%;
}

.detail-metrics {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.empty-state {
  padding: 40px 0;
  display: flex;
  justify-content: center;
}

/* Custom layout for Practice Center */
.quiz-container {
  height: calc(100vh - 84px); /* Adjust for header height */
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.practice-center-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-bottom: 0 !important;
}

.practice-center-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding-bottom: 0;
}

/* Ensure the row takes remaining height */
.practice-center-card .el-row {
  flex: 1;
  overflow: hidden;
  margin-bottom: 0 !important;
  height: 100%;
}

/* Ensure columns are full height and handle scrolling */
.practice-center-card .el-col {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* Left column: Practice History */
.practice-center-card .el-col:first-child {
  padding-right: 10px; /* Add some spacing if gutter isn't enough */
}

/* Right column: Stats/Overview */
.practice-center-card .el-col:last-child {
  overflow-y: auto;
  padding-right: 5px; /* Add padding for scrollbar */
}

/* Make table scrollable */
.practice-center-card .el-table {
  flex: 1;
  height: 0 !important; /* Allow flex to control height */
}

/* Ensure stats cards fit or scroll */
.practice-center-card .stats-card {
  margin-bottom: 20px;
}
</style>
